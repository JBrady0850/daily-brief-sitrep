# Daily Brief category library

Upload this file next to the prompt so the assistant can offer these categories.
Generated from app/data/library.js.

Starter packs:

- P1. **A little of everything**: Markets, science, travel, AI tools, an inspiring story and your town. (markets-economy, health-science, travel, ai-tools, inspiring, local-news)
- P2. **Technology professional**: Security, networks, cloud, AI and developer news, plus career skills. (cybersecurity, network-security, cloud-infrastructure, enterprise-ai, ai-tools, open-source, career-skills)
- P3. **Money and markets**: Personal finance, retirement rules, markets and housing. (personal-finance, retirement-planning, markets-economy, housing)
- P4. **Around town**: Your community, local government, weather and safety, plus good news and science. (local-news, local-government, local-weather, inspiring, health-science)
- P5. **Federal IT professional**: Ten desks for a federal IT professional: defense AI, workforce actions, the IT industry, corporate AI, AI tools, inspiring stories, pay and leave, retirement, your community, and network security. (defense-ai, federal-workforce, cybersecurity, enterprise-ai, ai-tools, inspiring, federal-pay, federal-retirement, local-news, network-security)

Categories:

*Technology*

1. `cybersecurity` **Cybersecurity and IT Industry**: Breaches, vulnerabilities, ransomware, patches and security updates that affect enterprise IT.
2. `network-security` **Network Security and Zero Trust**: Zero trust architecture, CISA and NSA guidance, firewall, VPN, identity and network hardening news.
3. `cloud-infrastructure` **Cloud and Data Centers**: Cloud platform launches, outages and pricing, plus data center capacity and power.
4. `enterprise-ai` **Corporate Enterprise AI**: How companies deploy AI: adoption, results, spending and workforce effects.
5. `ai-tools` **AI Tools and Prompting**: New features in AI assistants, prompting techniques and practical AI productivity tools.
6. `open-source` **Open Source and Developer Tools**: Open source releases, licensing changes and developer platform news.

*Government and defense*

7. `defense-ai` **Defense Enterprise AI**: Artificial intelligence across the Department of Defense and the military services.
8. `federal-workforce` **Federal Workforce Actions (RIF, VERA, VSIP)**: Reductions in force, early retirement and buyout offers, hiring freezes and restructuring in federal agencies.
9. `federal-pay` **Federal Pay, Leave and Benefits**: Federal pay raises or freezes, locality pay, annual leave rules, Open Season and benefit changes.
10. `federal-retirement` **Federal Retirement (FERS, TSP, FEHB)**: FERS annuities, the Thrift Savings Plan, retiree health coverage, COLA and OPM retirement processing.
11. `gov-tech` **Government Technology**: IT modernization, cloud, cybersecurity and AI programs in federal, state and local government.

*Money*

12. `personal-finance` **Personal Finance and Banking**: Savings rates, credit, mortgages, banking rules and consumer protection.
13. `retirement-planning` **Retirement Planning (401(k), IRA, Social Security)**: Social Security, Medicare, 401(k) and IRA rule changes and retirement income planning.
14. `markets-economy` **Markets and the Economy**: Stock market moves, interest rates, inflation, jobs and growth reports.
15. `housing` **Housing and Real Estate**: Mortgage rates, home prices, rents and the housing market.

*Career*

16. `career-skills` **Career Growth and Skills**: Certifications, in-demand skills, pay surveys and job market trends.

*Your area*

17. `local-news` **Local Community ({location})**: Community events, openings, schools and initiatives in your area. Crime and sports are left out.
18. `local-government` **Local Government ({location})**: City and county councils, budgets, ordinances, zoning and elections in your area.
19. `local-weather` **Weather and Safety ({location})**: Storms, flooding, closures, outages and emergency notices in your area.

*Life and world*

20. `inspiring` **Inspiring Personal Journeys**: True stories of people who overcame adversity, made a comeback or helped others.
21. `health-science` **Health and Science**: New research, medical findings, public health and space science.
22. `travel` **Travel**: Airlines, airports, cruises, national parks, passports and travel advisories.

## Details

### Cybersecurity and IT Industry (`cybersecurity`)

Breaches, vulnerabilities, ransomware, patches and security updates that affect enterprise IT.

- Queries: `(cybersecurity OR "data breach" OR ransomware OR vulnerability) enterprise` / `("zero-day" OR CVE OR "security update" OR patch) (Microsoft OR Cisco OR Google OR Apple)`
- Must mention one of (group 1): cybersecurity, cyber, breach, data breach, vulnerability, vulnerabilities, ransomware, malware, CVE, exploit, zero-day, hacker, hackers, hacking, phishing, patch, security update, cyberattack
- Publisher feeds: https://www.bleepingcomputer.com/feed/, https://feeds.feedburner.com/TheHackersNews

### Network Security and Zero Trust (`network-security`)

Zero trust architecture, CISA and NSA guidance, firewall, VPN, identity and network hardening news.

- Queries: `"zero trust" (network OR security OR architecture)` / `(CISA OR NSA) (advisory OR guidance OR directive) (network OR security)`
- Must mention one of (group 1): zero trust, CISA, NSA, network, networking, firewall, router, VPN, Active Directory, MFA, authentication, identity, advisory, hardening, segmentation, SASE

### Cloud and Data Centers (`cloud-infrastructure`)

Cloud platform launches, outages and pricing, plus data center capacity and power.

- Queries: `(AWS OR Azure OR "Google Cloud") (outage OR launch OR pricing OR region)` / `"data center" (capacity OR power OR construction OR investment)`
- Must mention one of (group 1): cloud, AWS, Azure, Google Cloud, data center, data centers, Kubernetes, outage, infrastructure, hyperscaler

### Corporate Enterprise AI (`enterprise-ai`)

How companies deploy AI: adoption, results, spending and workforce effects.

- Queries: `"enterprise AI" (deployment OR adoption OR ROI OR CEO OR companies)` / `(companies OR enterprises OR CEOs) ("AI agents" OR "generative AI") deployment`
- Must mention one of (group 1): AI, A.I., artificial intelligence, machine learning, generative AI, GenAI, LLM, large language model, agentic, AI agent, AI agents, chatbot
- Must mention one of (group 2): enterprise, corporate, company, companies, business, Fortune 500, CEO, CIO, CTO, ROI, adoption, deployment, workforce, firm, industry

### AI Tools and Prompting (`ai-tools`)

New features in AI assistants, prompting techniques and practical AI productivity tools.

- Queries: `(ChatGPT OR Claude OR Gemini OR Copilot OR Grok) (feature OR launches OR update OR tips)` / `("prompt engineering" OR "AI assistant" OR "AI tools") (productivity OR workflow OR tips)`
- Must mention one of (group 1): AI, A.I., artificial intelligence, machine learning, generative AI, GenAI, LLM, large language model, agentic, AI agent, AI agents, chatbot, Claude, ChatGPT, Gemini, Copilot, Grok, Anthropic, OpenAI
- Must mention one of (group 2): prompt, prompting, prompt engineering, tool, tools, assistant, workflow, automation, productivity, app, feature, features, launch, launches, launched, release, released, plugin, extension, update

### Open Source and Developer Tools (`open-source`)

Open source releases, licensing changes and developer platform news.

- Queries: `("open source" OR "open-source") (release OR project OR license)` / `(GitHub OR Python OR Linux OR Rust) (release OR update OR security)`
- Must mention one of (group 1): open source, open-source, GitHub, Linux, Python, JavaScript, Rust, developer, developers, repository, programming

### Defense Enterprise AI (`defense-ai`)

Artificial intelligence across the Department of Defense and the military services.

- Queries: `Pentagon military enterprise AI artificial intelligence deployment` / `(CDAO OR DISA OR DARPA OR Pentagon) AI strategy networks`
- Must mention one of (group 1): AI, A.I., artificial intelligence, machine learning, generative AI, GenAI, LLM, large language model, agentic, AI agent, AI agents, chatbot, autonomous, autonomy, algorithm
- Must mention one of (group 2): Pentagon, DoD, Department of War, Department of Defense, Army, Navy, Air Force, Marine Corps, Marines, Space Force, CDAO, DISA, DARPA, military, defense, warfighter, combatant command
- Publisher feeds: https://www.defenseone.com/rss/all/

### Federal Workforce Actions (RIF, VERA, VSIP) (`federal-workforce`)

Reductions in force, early retirement and buyout offers, hiring freezes and restructuring in federal agencies.

- Queries: `(RIF OR "reduction in force" OR VERA OR VSIP OR "deferred resignation" OR buyout OR layoffs) (federal OR agency OR OPM)` / `"federal employees" (layoffs OR RIF OR shutdown OR furlough OR "early retirement")`
- Must mention one of (group 1): RIF, reduction in force, reductions in force, VERA, VSIP, early retirement, buyout, buyouts, deferred resignation, DRP, layoff, layoffs, furlough, workforce reduction, workforce cuts, job cuts, hiring freeze, restructuring, reorganization, downsizing, probationary, Schedule F, shutdown
- Must mention one of (group 2): federal, civilian, civil service, OPM, agency, agencies, government, DoD, Pentagon, Department of War
- Publisher feeds: https://www.govexec.com/rss/workforce/, https://federalnewsnetwork.com/category/workforce/feed/

### Federal Pay, Leave and Benefits (`federal-pay`)

Federal pay raises or freezes, locality pay, annual leave rules, Open Season and benefit changes.

- Queries: `("federal employees" OR "federal workers" OR feds OR OPM) ("pay raise" OR "pay freeze" OR "locality pay" OR "annual leave" OR "Open Season")` / `("federal employees" OR OPM) (benefits OR FEHB OR leave OR "pay period") (deadline OR change OR rule)`
- Must mention one of (group 1): pay raise, pay freeze, pay increase, pay adjustment, locality pay, General Schedule, salary, wage, annual leave, sick leave, use-or-lose, use or lose, lump sum, lump-sum, leave year, pay period, Open Season, FEHB, FEGLI, FEDVIP, TSP, benefits, administrative leave, step increase, within-grade
- Must mention one of (group 2): federal, feds, OPM, General Schedule, civil service, federal workforce, federal employees, federal workers, agency, agencies
- Leave out: job seekers, apply now, job posting, job opening
- Publisher feeds: https://www.govexec.com/rss/pay-benefits/

### Federal Retirement (FERS, TSP, FEHB) (`federal-retirement`)

FERS annuities, the Thrift Savings Plan, retiree health coverage, COLA and OPM retirement processing.

- Queries: `(FERS OR TSP OR FEHB OR "federal retirees" OR "federal annuity") (retirement OR COLA OR premiums OR withdrawal)` / `(OPM OR "federal retirement") ("retirement processing" OR backlog OR "retirement application" OR annuity)`
- Must mention one of (group 1): FERS, TSP, Thrift Savings Plan, FEHB, PSHB, COLA, cost-of-living, annuity, annuitant, annuitants, pension, Medicare, FEGLI, retirement, retire, retirees, survivor benefit, FERS supplement, Open Season, G Fund, C Fund, L Fund, withdrawal, premium, premiums, retirement processing
- Must mention one of (group 2): federal, feds, FERS, CSRS, TSP, FEHB, OPM, civil service, federal retirees, federal employees, federal workers, Thrift Savings Plan
- Leave out: Bitcoin, crypto, meme stock, sponsored content
- Publisher feeds: https://www.fedsmith.com/feed/, https://www.myfederalretirement.com/feed/, https://www.fedimpact.com/feed/, https://federalnewsnetwork.com/category/retirement/feed/

### Government Technology (`gov-tech`)

IT modernization, cloud, cybersecurity and AI programs in federal, state and local government.

- Queries: `("federal IT" OR "government technology" OR "agency CIO" OR "state CIO") (modernization OR cloud OR cybersecurity OR AI)` / `(agency OR agencies OR government) ("IT modernization" OR "digital services" OR "cloud migration")`
- Must mention one of (group 1): federal, government, agency, agencies, state government, public sector, city, county, Pentagon, DoD
- Must mention one of (group 2): technology, IT, modernization, cloud, cybersecurity, AI, software, digital, data, network, networks
- Publisher feeds: https://www.nextgov.com/rss/all/

### Personal Finance and Banking (`personal-finance`)

Savings rates, credit, mortgages, banking rules and consumer protection.

- Queries: `(savings OR mortgage OR "credit card" OR "interest rates") consumers` / `(FDIC OR CFPB OR "Federal Reserve") (consumers OR banking OR rule)`
- Must mention one of (group 1): savings, mortgage, mortgages, credit card, credit cards, credit score, interest rate, interest rates, inflation, FDIC, CFPB, Federal Reserve, bank, banks, banking, budget, debt, loan, loans
- Leave out: Bitcoin, crypto, sponsored content, meme stock

### Retirement Planning (401(k), IRA, Social Security) (`retirement-planning`)

Social Security, Medicare, 401(k) and IRA rule changes and retirement income planning.

- Queries: `("Social Security" OR Medicare) (COLA OR "Part B" OR "retirement age" OR benefits)` / `("401(k)" OR IRA OR Roth) (rules OR limits OR "required minimum distribution" OR contribution)`
- Must mention one of (group 1): Social Security, Medicare, 401(k), IRA, IRAs, Roth, retirement, retire, retirees, pension, annuity, required minimum distribution, RMD, COLA
- Leave out: Bitcoin, crypto, sponsored content

### Markets and the Economy (`markets-economy`)

Stock market moves, interest rates, inflation, jobs and growth reports.

- Queries: `(stocks OR "S&P 500" OR Nasdaq OR Dow) (close OR rally OR selloff OR record)` / `(inflation OR "jobs report" OR GDP OR "Federal Reserve") economy`
- Must mention one of (group 1): stocks, stock market, S&P 500, Nasdaq, Dow, Treasury, yields, inflation, jobs report, unemployment, GDP, Federal Reserve, economy, recession, earnings, interest rates
- Leave out: sponsored content

### Housing and Real Estate (`housing`)

Mortgage rates, home prices, rents and the housing market.

- Queries: `("mortgage rates" OR "home prices" OR "housing market")` / `(rent OR rents OR "home sales" OR "housing starts") report`
- Must mention one of (group 1): mortgage, mortgages, mortgage rates, home prices, housing, real estate, rent, rents, home sales, homebuyers, housing starts
- Leave out: sponsored content

### Career Growth and Skills (`career-skills`)

Certifications, in-demand skills, pay surveys and job market trends.

- Queries: `(certification OR upskilling OR "skills gap") (IT OR technology OR workers)` / `(salary OR wages OR pay) (survey OR report) (IT OR tech OR technology)`
- Must mention one of (group 1): career, careers, certification, certifications, skills, upskilling, reskilling, salary, salaries, wages, promotion, hiring, job market, jobs, workforce
- Must mention one of (group 2): IT, tech, technology, workers, employees, employers, professionals, workforce, job, jobs, career, careers, employment, labor market, job market, hiring
- Leave out: apply now, job posting, job opening, hiring event, election, elections, ballot

### Local Community ({location}) (`local-news`)

Community events, openings, schools and initiatives in your area. Crime and sports are left out.

- Queries: `"{location}" (community OR council OR school OR event OR opens)` / `"{location}" (announces OR initiative OR project OR program)`
- Must mention one of (group 1): {local_terms}
- Leave out: football, basketball, baseball, softball, volleyball, soccer, touchdown, playoff, quarterback, shooting, arrested, arrest, homicide, deputies, sentenced, prison, jail, charged, crash, killed, fatal, burglary, robbery, theft, suspect, stabbing

### Local Government ({location}) (`local-government`)

City and county councils, budgets, ordinances, zoning and elections in your area.

- Queries: `"{location}" (council OR commission OR budget OR ordinance OR election)` / `"{location}" (mayor OR commissioners OR zoning OR "school board")`
- Must mention one of (group 1): {local_terms}
- Must mention one of (group 2): council, commission, commissioners, budget, ordinance, election, mayor, county, city, school board, zoning, permit, vote
- Leave out: football, basketball, baseball, homicide, shooting

### Weather and Safety ({location}) (`local-weather`)

Storms, flooding, closures, outages and emergency notices in your area.

- Queries: `"{location}" (storm OR hurricane OR flooding OR tornado OR wildfire)` / `"{location}" ("boil water" OR closure OR outage OR evacuation)`
- Must mention one of (group 1): {local_terms}
- Must mention one of (group 2): storm, storms, hurricane, tornado, flood, flooding, weather, evacuation, boil water, closure, closures, outage, outages, wildfire

### Inspiring Personal Journeys (`inspiring`)

True stories of people who overcame adversity, made a comeback or helped others.

- Queries: `(inspiring OR comeback OR overcame OR resilience) story` / `("against the odds" OR "beat the odds" OR survivor OR perseverance) inspiring`
- Must mention one of (group 1): comeback, overcame, overcome, overcomes, overcoming, resilience, resilient, inspiring, inspirational, against the odds, beat the odds, triumph, persevere, perseverance, persevered, survivor, turnaround, adversity, second chance, defied
- Leave out: album, Reels, vlog, lyrics, trailer, episode, tour dates, recap, finale, spoiler, box office, climate resilience, cyber resilience, supply chain resilience, stocks, shares, market rally, novel, webtoon

### Health and Science (`health-science`)

New research, medical findings, public health and space science.

- Queries: `(study OR researchers OR scientists) (health OR medicine OR disease)` / `(NASA OR telescope OR space) discovery`
- Must mention one of (group 1): study, researchers, scientists, research, trial, FDA, NIH, CDC, NASA, discovery, vaccine, disease, medicine, health
- Leave out: sponsored content, supplement deal

### Travel (`travel`)

Airlines, airports, cruises, national parks, passports and travel advisories.

- Queries: `(airlines OR airports OR TSA OR "national parks") travelers` / `(cruise OR "travel advisory" OR passport) travelers`
- Must mention one of (group 1): airline, airlines, airport, airports, TSA, flight, flights, travel, travelers, cruise, cruises, national park, national parks, passport, hotel, hotels
- Leave out: sponsored content
