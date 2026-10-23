"""Mail settings and SMTP sending (with a fake server)."""
import json

import pytest

from dailybrief import mailer as M, store

ENV = {"SMTP_HOST": "smtp.example.com", "SMTP_USER": "me@example.com", "SMTP_PASSWORD": "abcd efgh ijkl mnop",
       "MAIL_TO": "a@example.com, b@example.com"}


class FakeSMTP:
    log = []

    def __init__(self, host, port, timeout=None, context=None):
        FakeSMTP.log.append(("open", type(self).__name__, host, port))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        FakeSMTP.log.append(("close",))

    def ehlo(self):
        pass

    def starttls(self, context=None):
        FakeSMTP.log.append(("starttls",))

    def login(self, user, password):
        FakeSMTP.log.append(("login", user, password))

    def send_message(self, msg, from_addr=None, to_addrs=None):
        FakeSMTP.log.append(("send", from_addr, tuple(to_addrs), msg["Subject"]))


class FakeSSL(FakeSMTP):
    pass


def test_settings_from_environment():
    s = M.load_settings(env=ENV, saved={})
    assert (s.host, s.port, s.security, s.sender, s.recipients) == ("smtp.example.com", 587, "starttls", "me@example.com",
                                                                     ["a@example.com", "b@example.com"])
    assert "abcd" not in repr(s)
    assert M.load_settings(env=dict(ENV, SMTP_PORT="465"), saved={}).security == "ssl"


def test_missing_settings_are_named_without_the_password():
    with pytest.raises(M.MailConfigError) as e:
        M.load_settings(env={"SMTP_PASSWORD": "secret-value"}, saved={})
    assert "SMTP_HOST" in str(e.value) and "MAIL_TO" in str(e.value) and "secret-value" not in str(e.value)
    with pytest.raises(M.MailConfigError):
        M.load_settings(env=dict(ENV, MAIL_TO="not-an-address"), saved={})


def test_message_has_text_and_html_parts():
    msg = M.build_message("Subject é", "plain", "<p>html</p>", "me@example.com", ["a@example.com"], "Morning Brief")
    assert msg.is_multipart() and [p.get_content_type() for p in msg.iter_parts()] == ["text/plain", "text/html"]
    assert msg["From"] == "Morning Brief <me@example.com>"


@pytest.mark.parametrize("port,cls,starttls", [(587, "FakeSMTP", True), (465, "FakeSSL", False)])
def test_send_uses_tls(port, cls, starttls):
    FakeSMTP.log = []
    s = M.load_settings(env=dict(ENV, SMTP_PORT=str(port)), saved={})
    M.send(M.build_message("S", "t", "<p>h</p>", s.sender, s.recipients), s, smtp_factory=FakeSMTP, ssl_factory=FakeSSL)
    assert FakeSMTP.log[0][1] == cls
    assert (("starttls",) in FakeSMTP.log) is starttls
    assert ("login", "me@example.com", "abcd efgh ijkl mnop") in FakeSMTP.log
    assert ("send", "me@example.com", ("a@example.com", "b@example.com"), "S") in FakeSMTP.log


def test_saved_settings_keep_the_password_private():
    M.save_settings({"host": "smtp.example.com", "port": "587", "user": "me@example.com", "password": "pw-one", "to": "a@example.com"})
    M.save_settings({"host": "smtp.example.com", "password": ""})  # empty keeps the saved password
    saved = json.loads(store.path(store.SMTP).read_text())
    assert saved["password"] == "pw-one"
    pub = M.public_settings()
    assert pub["has_password"] and pub["configured"] and "password" not in pub
    assert "pw-one" not in json.dumps(pub)


class _SmtpSink:
    """A minimal SMTP server on 127.0.0.1 that stores what it receives, so the
    real smtplib path is exercised end to end without any mail provider."""

    def __init__(self):
        import socket
        import threading
        self.messages = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        conn, _ = self.sock.accept()
        f = conn.makefile("rwb")

        def say(line):
            f.write(line.encode() + b"\r\n")
            f.flush()

        say("220 sink ready")
        rcpts, data_mode, buf = [], False, []
        while True:
            raw = f.readline()
            if not raw:
                break
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if data_mode:
                if line == ".":
                    self.messages.append((rcpts[:], "\r\n".join(buf)))
                    data_mode, buf = False, []
                    say("250 queued")
                else:
                    buf.append(line[1:] if line.startswith("..") else line)
                continue
            cmd = line[:4].upper()
            if cmd in ("EHLO", "HELO"):
                say("250 sink")
            elif cmd == "MAIL":
                rcpts = []
                say("250 ok")
            elif cmd == "RCPT":
                rcpts.append(line.split(":", 1)[1].strip().strip("<>"))
                say("250 ok")
            elif cmd == "DATA":
                data_mode = True
                say("354 go ahead")
            elif cmd == "QUIT":
                say("221 bye")
                break
            else:
                say("250 ok")
        conn.close()
        self.sock.close()


def test_real_smtp_session_against_a_local_sink(sample_brief):
    from dailybrief import render
    sink = _SmtpSink()
    env = {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(sink.port), "SMTP_USER": "me@example.com", "SMTP_PASSWORD": "unused",
           "SMTP_SECURITY": "none", "MAIL_TO": "a@example.com, b@example.com"}
    s = M.load_settings(env=env, saved={})
    out = render.render(sample_brief)
    M.send(M.build_message(out["subject"], out["text"], out["html"], s.sender, s.recipients, "Morning Brief"), s, timeout=10)
    sink.thread.join(5)
    assert len(sink.messages) == 1
    rcpts, data = sink.messages[0]
    assert rcpts == ["a@example.com", "b@example.com"]
    assert "Content-Type: multipart/alternative" in data and "text/html" in data and "From: Morning Brief <me@example.com>" in data


def test_a_saved_password_never_goes_to_a_new_server():
    M.save_settings({"host": "smtp.example.com", "port": "587", "user": "me@example.com", "password": "real-pass", "to": "a@example.com"})
    M.save_settings({"host": "smtp.attacker.example", "password": ""})
    saved = json.loads(store.path(store.SMTP).read_text())
    assert saved["password"] == "" and not M.public_settings()["has_password"]
    M.save_settings({"host": "smtp.attacker.example", "password": "typed-again"})
    M.save_settings({"user": "other@example.com"})
    assert json.loads(store.path(store.SMTP).read_text())["password"] == ""


def test_private_files_are_owner_only_from_the_start():
    import os
    import stat
    if os.name != "posix":
        return
    M.save_settings({"host": "smtp.example.com", "password": "pw"})
    mode = stat.S_IMODE(os.stat(store.path(store.SMTP)).st_mode)
    assert mode == 0o600
