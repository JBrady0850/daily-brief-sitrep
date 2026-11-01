/* Theme (0.14.0): runs in <head> before first paint. Auto follows the device; Light and Dark are saved in this
   browser only (localStorage db.theme.v1). */
(function () {
  var KEY = "db.theme.v1";
  function get() { try { var v = localStorage.getItem(KEY); return v === "light" || v === "dark" ? v : "auto"; } catch (e) { return "auto"; } }
  function apply(v) { if (v === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", v); }
  apply(get());
  document.addEventListener("DOMContentLoaded", function () {
    var sel = document.getElementById("theme-sel");
    if (!sel) return;
    sel.value = get();
    sel.addEventListener("change", function () {
      var v = sel.value === "light" || sel.value === "dark" ? sel.value : "auto";
      try { if (v === "auto") localStorage.removeItem(KEY); else localStorage.setItem(KEY, v); } catch (e) { }
      apply(v);
    });
  });
})();
