/* Daily Brief category library. Plain JSON after the equals sign, so the app
   reads it in any browser (including file://) and the Python tools read the
   same file. Edit here; see docs/CATEGORIES.md. */
window.DB_LIBRARY = {
 "version": 1,
 "groups": [
  {
   "id": "tech",
   "name": "Technology"
  },
  {
   "id": "gov",
   "name": "Government and defense"
  },
  {
   "id": "money",
   "name": "Money"
  },
  {
   "id": "career",
   "name": "Career"
  },
  {
   "id": "local",
   "name": "Your area"
  },
  {
   "id": "life",
   "name": "Life and world"
  }
 ],
 "categories": [
  {
   "id": "cybersecurity",
   "group": "tech",
   "name": "Cybersecurity and IT Industry",
   "description": "Breaches, vulnerabilities, ransomware, patches and security updates that affect enterprise IT.",
   "queries": [
    "(cybersecurity OR \"data breach\" OR ransomware OR vulnerability) enterprise",
    "(\"zero-day\" OR CVE OR \"security update\" OR patch) (Microsoft OR Cisco OR Google OR Apple)"
   ],
   "require": [
    [
     "cybersecurity",
     "cyber",
     "breach",
     "data breach",
     "vulnerability",
     "vulnerabilities",
     "ransomware",
     "malware",
     "CVE",
     "exploit",
     "zero-day",
     "hacker",
     "hackers",
     "hacking",
     "phishing",
     "patch",
     "security update",
     "cyberattack"
    ]
   ],
   "exclude": [],
   "feeds": [
    "https://www.bleepingcomputer.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews"
   ],
   "color": "#1f3a5f",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "network-security",
   "group": "tech",
   "name": "Network Security and Zero Trust",
   "description": "Zero trust architecture, CISA and NSA guidance, firewall, VPN, identity and network hardening news.",
   "queries": [
    "\"zero trust\" (network OR security OR architecture)",
    "(CISA OR NSA) (advisory OR guidance OR directive) (network OR security)"
   ],
   "require": [
    [
     "zero trust",
     "CISA",
     "NSA",
     "network",
     "networking",
     "firewall",
     "router",
     "VPN",
     "Active Directory",
     "MFA",
     "authentication",
     "identity",
     "advisory",
     "hardening",
     "segmentation",
     "SASE"
    ]
   ],
   "exclude": [],
   "feeds": [],
   "color": "#34495e",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "cloud-infrastructure",
   "group": "tech",
   "name": "Cloud and Data Centers",
   "description": "Cloud platform launches, outages and pricing, plus data center capacity and power.",
   "queries": [
    "(AWS OR Azure OR \"Google Cloud\") (outage OR launch OR pricing OR region)",
    "\"data center\" (capacity OR power OR construction OR investment)"
   ],
   "require": [
    [
     "cloud",
     "AWS",
     "Azure",
     "Google Cloud",
     "data center",
     "data centers",
     "Kubernetes",
     "outage",
     "infrastructure",
     "hyperscaler"
    ]
   ],
   "exclude": [],
   "feeds": [],
   "color": "#0b5e8f",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "enterprise-ai",
   "group": "tech",
   "name": "Corporate Enterprise AI",
   "description": "How companies deploy AI: adoption, results, spending and workforce effects.",
   "queries": [
    "\"enterprise AI\" (deployment OR adoption OR ROI OR CEO OR companies)",
    "(companies OR enterprises OR CEOs) (\"AI agents\" OR \"generative AI\") deployment"
   ],
   "require": [
    [
     "AI",
     "A.I.",
     "artificial intelligence",
     "machine learning",
     "generative AI",
     "GenAI",
     "LLM",
     "large language model",
     "agentic",
     "AI agent",
     "AI agents",
     "chatbot"
    ],
    [
     "enterprise",
     "corporate",
     "company",
     "companies",
     "business",
     "Fortune 500",
     "CEO",
     "CIO",
     "CTO",
     "ROI",
     "adoption",
     "deployment",
     "workforce",
     "firm",
     "industry"
    ]
   ],
   "exclude": [],
   "skip_listicles": true,
   "feeds": [],
   "color": "#5b3485",
   "needs_location": false
  },
  {
   "id": "ai-tools",
   "group": "tech",
   "name": "AI Tools and Prompting",
   "description": "New features in AI assistants, prompting techniques and practical AI productivity tools.",
   "queries": [
    "(ChatGPT OR Claude OR Gemini OR Copilot OR Grok) (feature OR launches OR update OR tips)",
    "(\"prompt engineering\" OR \"AI assistant\" OR \"AI tools\") (productivity OR workflow OR tips)"
   ],
   "require": [
    [
     "AI",
     "A.I.",
     "artificial intelligence",
     "machine learning",
     "generative AI",
     "GenAI",
     "LLM",
     "large language model",
     "agentic",
     "AI agent",
     "AI agents",
     "chatbot",
     "Claude",
     "ChatGPT",
     "Gemini",
     "Copilot",
     "Grok",
     "Anthropic",
     "OpenAI"
    ],
    [
     "prompt",
     "prompting",
     "prompt engineering",
     "tool",
     "tools",
     "assistant",
     "workflow",
     "automation",
     "productivity",
     "app",
     "feature",
     "features",
     "launch",
     "launches",
     "launched",
     "release",
     "released",
     "plugin",
     "extension",
     "update"
    ]
   ],
   "exclude": [],
   "skip_listicles": true,
   "feeds": [],
   "color": "#a04000",
   "needs_location": false
  },
  {
   "id": "open-source",
   "group": "tech",
   "name": "Open Source and Developer Tools",
   "description": "Open source releases, licensing changes and developer platform news.",
   "queries": [
    "(\"open source\" OR \"open-source\") (release OR project OR license)",
    "(GitHub OR Python OR Linux OR Rust) (release OR update OR security)"
   ],
   "require": [
    [
     "open source",
     "open-source",
     "GitHub",
     "Linux",
     "Python",
     "JavaScript",
     "Rust",
     "developer",
     "developers",
     "repository",
     "programming"
    ]
   ],
   "exclude": [],
   "feeds": [],
   "color": "#1b6e3d",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "defense-ai",
   "group": "gov",
   "name": "Defense Enterprise AI",
   "description": "Artificial intelligence across the Department of Defense and the military services.",
   "queries": [
    "Pentagon military enterprise AI artificial intelligence deployment",
    "(CDAO OR DISA OR DARPA OR Pentagon) AI strategy networks"
   ],
   "require": [
    [
     "AI",
     "A.I.",
     "artificial intelligence",
     "machine learning",
     "generative AI",
     "GenAI",
     "LLM",
     "large language model",
     "agentic",
     "AI agent",
     "AI agents",
     "chatbot",
     "autonomous",
     "autonomy",
     "algorithm"
    ],
    [
     "Pentagon",
     "DoD",
     "Department of War",
     "Department of Defense",
     "Army",
     "Navy",
     "Air Force",
     "Marine Corps",
     "Marines",
     "Space Force",
     "CDAO",
     "DISA",
     "DARPA",
     "military",
     "defense",
     "warfighter",
     "combatant command"
    ]
   ],
   "exclude": [],
   "feeds": [
    "https://www.defenseone.com/rss/all/"
   ],
   "color": "#1f3a5f",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "federal-workforce",
   "group": "gov",
   "name": "Federal Workforce Actions (RIF, VERA, VSIP)",
   "description": "Reductions in force, early retirement and buyout offers, hiring freezes and restructuring in federal agencies.",
   "queries": [
    "(RIF OR \"reduction in force\" OR VERA OR VSIP OR \"deferred resignation\" OR buyout OR layoffs) (federal OR agency OR OPM)",
    "\"federal employees\" (layoffs OR RIF OR shutdown OR furlough OR \"early retirement\")"
   ],
   "require": [
    [
     "RIF",
     "reduction in force",
     "reductions in force",
     "VERA",
     "VSIP",
     "early retirement",
     "buyout",
     "buyouts",
     "deferred resignation",
     "DRP",
     "layoff",
     "layoffs",
     "furlough",
     "workforce reduction",
     "workforce cuts",
     "job cuts",
     "hiring freeze",
     "restructuring",
     "reorganization",
     "downsizing",
     "probationary",
     "Schedule F",
     "shutdown"
    ],
    [
     "federal",
     "civilian",
     "civil service",
     "OPM",
     "agency",
     "agencies",
     "government",
     "DoD",
     "Pentagon",
     "Department of War"
    ]
   ],
   "exclude": [],
   "feeds": [
    "https://www.govexec.com/rss/workforce/",
    "https://federalnewsnetwork.com/category/workforce/feed/"
   ],
   "color": "#0b5e8f",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "federal-pay",
   "group": "gov",
   "name": "Federal Pay, Leave and Benefits",
   "description": "Federal pay raises or freezes, locality pay, annual leave rules, Open Season and benefit changes.",
   "queries": [
    "(\"federal employees\" OR \"federal workers\" OR feds OR OPM) (\"pay raise\" OR \"pay freeze\" OR \"locality pay\" OR \"annual leave\" OR \"Open Season\")",
    "(\"federal employees\" OR OPM) (benefits OR FEHB OR leave OR \"pay period\") (deadline OR change OR rule)"
   ],
   "require": [
    [
     "pay raise",
     "pay freeze",
     "pay increase",
     "pay adjustment",
     "locality pay",
     "General Schedule",
     "salary",
     "wage",
     "annual leave",
     "sick leave",
     "use-or-lose",
     "use or lose",
     "lump sum",
     "lump-sum",
     "leave year",
     "pay period",
     "Open Season",
     "FEHB",
     "FEGLI",
     "FEDVIP",
     "TSP",
     "benefits",
     "administrative leave",
     "step increase",
     "within-grade"
    ],
    [
     "federal",
     "feds",
     "OPM",
     "General Schedule",
     "civil service",
     "federal workforce",
     "federal employees",
     "federal workers",
     "agency",
     "agencies"
    ]
   ],
   "exclude": [
    "job seekers",
    "apply now",
    "job posting",
    "job opening"
   ],
   "feeds": [
    "https://www.govexec.com/rss/pay-benefits/"
   ],
   "color": "#1b6e3d",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "federal-retirement",
   "group": "gov",
   "name": "Federal Retirement (FERS, TSP, FEHB)",
   "description": "FERS annuities, the Thrift Savings Plan, retiree health coverage, COLA and OPM retirement processing.",
   "queries": [
    "(FERS OR TSP OR FEHB OR \"federal retirees\" OR \"federal annuity\") (retirement OR COLA OR premiums OR withdrawal)",
    "(OPM OR \"federal retirement\") (\"retirement processing\" OR backlog OR \"retirement application\" OR annuity)"
   ],
   "require": [
    [
     "FERS",
     "TSP",
     "Thrift Savings Plan",
     "FEHB",
     "PSHB",
     "COLA",
     "cost-of-living",
     "annuity",
     "annuitant",
     "annuitants",
     "pension",
     "Medicare",
     "FEGLI",
     "retirement",
     "retire",
     "retirees",
     "survivor benefit",
     "FERS supplement",
     "Open Season",
     "G Fund",
     "C Fund",
     "L Fund",
     "withdrawal",
     "premium",
     "premiums",
     "retirement processing"
    ],
    [
     "federal",
     "feds",
     "FERS",
     "CSRS",
     "TSP",
     "FEHB",
     "OPM",
     "civil service",
     "federal retirees",
     "federal employees",
     "federal workers",
     "Thrift Savings Plan"
    ]
   ],
   "exclude": [
    "Bitcoin",
    "crypto",
    "meme stock",
    "sponsored content"
   ],
   "feeds": [
    "https://www.fedsmith.com/feed/",
    "https://www.myfederalretirement.com/feed/",
    "https://www.fedimpact.com/feed/",
    "https://federalnewsnetwork.com/category/retirement/feed/"
   ],
   "color": "#922b21",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "gov-tech",
   "group": "gov",
   "name": "Government Technology",
   "description": "IT modernization, cloud, cybersecurity and AI programs in federal, state and local government.",
   "queries": [
    "(\"federal IT\" OR \"government technology\" OR \"agency CIO\" OR \"state CIO\") (modernization OR cloud OR cybersecurity OR AI)",
    "(agency OR agencies OR government) (\"IT modernization\" OR \"digital services\" OR \"cloud migration\")"
   ],
   "require": [
    [
     "federal",
     "government",
     "agency",
     "agencies",
     "state government",
     "public sector",
     "city",
     "county",
     "Pentagon",
     "DoD"
    ],
    [
     "technology",
     "IT",
     "modernization",
     "cloud",
     "cybersecurity",
     "AI",
     "software",
     "digital",
     "data",
     "network",
     "networks"
    ]
   ],
   "exclude": [],
   "feeds": [
    "https://www.nextgov.com/rss/all/"
   ],
   "color": "#34495e",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "personal-finance",
   "group": "money",
   "name": "Personal Finance and Banking",
   "description": "Savings rates, credit, mortgages, banking rules and consumer protection.",
   "queries": [
    "(savings OR mortgage OR \"credit card\" OR \"interest rates\") consumers",
    "(FDIC OR CFPB OR \"Federal Reserve\") (consumers OR banking OR rule)"
   ],
   "require": [
    [
     "savings",
     "mortgage",
     "mortgages",
     "credit card",
     "credit cards",
     "credit score",
     "interest rate",
     "interest rates",
     "inflation",
     "FDIC",
     "CFPB",
     "Federal Reserve",
     "bank",
     "banks",
     "banking",
     "budget",
     "debt",
     "loan",
     "loans"
    ]
   ],
   "exclude": [
    "Bitcoin",
    "crypto",
    "sponsored content",
    "meme stock"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#1d6aa0",
   "needs_location": false
  },
  {
   "id": "retirement-planning",
   "group": "money",
   "name": "Retirement Planning (401(k), IRA, Social Security)",
   "description": "Social Security, Medicare, 401(k) and IRA rule changes and retirement income planning.",
   "queries": [
    "(\"Social Security\" OR Medicare) (COLA OR \"Part B\" OR \"retirement age\" OR benefits)",
    "(\"401(k)\" OR IRA OR Roth) (rules OR limits OR \"required minimum distribution\" OR contribution)"
   ],
   "require": [
    [
     "Social Security",
     "Medicare",
     "401(k)",
     "IRA",
     "IRAs",
     "Roth",
     "retirement",
     "retire",
     "retirees",
     "pension",
     "annuity",
     "required minimum distribution",
     "RMD",
     "COLA"
    ]
   ],
   "exclude": [
    "Bitcoin",
    "crypto",
    "sponsored content"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#922b21",
   "needs_location": false
  },
  {
   "id": "markets-economy",
   "group": "money",
   "name": "Markets and the Economy",
   "description": "Stock market moves, interest rates, inflation, jobs and growth reports.",
   "queries": [
    "(stocks OR \"S&P 500\" OR Nasdaq OR Dow) (close OR rally OR selloff OR record)",
    "(inflation OR \"jobs report\" OR GDP OR \"Federal Reserve\") economy"
   ],
   "require": [
    [
     "stocks",
     "stock market",
     "S&P 500",
     "Nasdaq",
     "Dow",
     "Treasury",
     "yields",
     "inflation",
     "jobs report",
     "unemployment",
     "GDP",
     "Federal Reserve",
     "economy",
     "recession",
     "earnings",
     "interest rates"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "feeds": [],
   "color": "#0f6e5c",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "housing",
   "group": "money",
   "name": "Housing and Real Estate",
   "description": "Mortgage rates, home prices, rents and the housing market.",
   "queries": [
    "(\"mortgage rates\" OR \"home prices\" OR \"housing market\")",
    "(rent OR rents OR \"home sales\" OR \"housing starts\") report"
   ],
   "require": [
    [
     "mortgage",
     "mortgages",
     "mortgage rates",
     "home prices",
     "housing",
     "real estate",
     "rent",
     "rents",
     "home sales",
     "homebuyers",
     "housing starts"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#6b4f2a",
   "needs_location": false
  },
  {
   "id": "career-skills",
   "group": "career",
   "name": "Career Growth and Skills",
   "description": "Certifications, in-demand skills, pay surveys and job market trends.",
   "queries": [
    "(certification OR upskilling OR \"skills gap\") (IT OR technology OR workers)",
    "(salary OR wages OR pay) (survey OR report) (IT OR tech OR technology)"
   ],
   "require": [
    [
     "career",
     "careers",
     "certification",
     "certifications",
     "skills",
     "upskilling",
     "reskilling",
     "salary",
     "salaries",
     "wages",
     "promotion",
     "hiring",
     "job market",
     "jobs",
     "workforce"
    ],
    [
     "IT",
     "tech",
     "technology",
     "workers",
     "employees",
     "employers",
     "professionals",
     "workforce",
     "job",
     "jobs",
     "career",
     "careers",
     "employment",
     "labor market",
     "job market",
     "hiring"
    ]
   ],
   "exclude": [
    "apply now",
    "job posting",
    "job opening",
    "hiring event",
    "election",
    "elections",
    "ballot"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#1b6e3d",
   "needs_location": false
  },
  {
   "id": "local-news",
   "group": "local",
   "name": "Local Community ({location})",
   "description": "Community events, openings, schools and initiatives in your area. Crime and sports are left out.",
   "queries": [
    "\"{location}\" (community OR council OR school OR event OR opens)",
    "\"{location}\" (announces OR initiative OR project OR program)"
   ],
   "require": [
    [
     "{local_terms}"
    ]
   ],
   "exclude": [
    "football",
    "basketball",
    "baseball",
    "softball",
    "volleyball",
    "soccer",
    "touchdown",
    "playoff",
    "quarterback",
    "shooting",
    "arrested",
    "arrest",
    "homicide",
    "deputies",
    "sentenced",
    "prison",
    "jail",
    "charged",
    "crash",
    "killed",
    "fatal",
    "burglary",
    "robbery",
    "theft",
    "suspect",
    "stabbing"
   ],
   "feeds": [],
   "color": "#1d6aa0",
   "needs_location": true,
   "skip_listicles": false
  },
  {
   "id": "local-government",
   "group": "local",
   "name": "Local Government ({location})",
   "description": "City and county councils, budgets, ordinances, zoning and elections in your area.",
   "queries": [
    "\"{location}\" (council OR commission OR budget OR ordinance OR election)",
    "\"{location}\" (mayor OR commissioners OR zoning OR \"school board\")"
   ],
   "require": [
    [
     "{local_terms}"
    ],
    [
     "council",
     "commission",
     "commissioners",
     "budget",
     "ordinance",
     "election",
     "mayor",
     "county",
     "city",
     "school board",
     "zoning",
     "permit",
     "vote"
    ]
   ],
   "exclude": [
    "football",
    "basketball",
    "baseball",
    "homicide",
    "shooting"
   ],
   "feeds": [],
   "color": "#0b5e8f",
   "needs_location": true,
   "skip_listicles": false
  },
  {
   "id": "local-weather",
   "group": "local",
   "name": "Weather and Safety ({location})",
   "description": "Storms, flooding, closures, outages and emergency notices in your area.",
   "queries": [
    "\"{location}\" (storm OR hurricane OR flooding OR tornado OR wildfire)",
    "\"{location}\" (\"boil water\" OR closure OR outage OR evacuation)"
   ],
   "require": [
    [
     "{local_terms}"
    ],
    [
     "storm",
     "storms",
     "hurricane",
     "tornado",
     "flood",
     "flooding",
     "weather",
     "evacuation",
     "boil water",
     "closure",
     "closures",
     "outage",
     "outages",
     "wildfire"
    ]
   ],
   "exclude": [],
   "feeds": [],
   "color": "#34495e",
   "needs_location": true,
   "skip_listicles": false
  },
  {
   "id": "inspiring",
   "group": "life",
   "name": "Inspiring Personal Journeys",
   "description": "True stories of people who overcame adversity, made a comeback or helped others.",
   "queries": [
    "(inspiring OR comeback OR overcame OR resilience) story",
    "(\"against the odds\" OR \"beat the odds\" OR survivor OR perseverance) inspiring"
   ],
   "require": [
    [
     "comeback",
     "overcame",
     "overcome",
     "overcomes",
     "overcoming",
     "resilience",
     "resilient",
     "inspiring",
     "inspirational",
     "against the odds",
     "beat the odds",
     "triumph",
     "persevere",
     "perseverance",
     "persevered",
     "survivor",
     "turnaround",
     "adversity",
     "second chance",
     "defied"
    ]
   ],
   "exclude": [
    "album",
    "Reels",
    "vlog",
    "lyrics",
    "trailer",
    "episode",
    "tour dates",
    "recap",
    "finale",
    "spoiler",
    "box office",
    "climate resilience",
    "cyber resilience",
    "supply chain resilience",
    "stocks",
    "shares",
    "market rally",
    "novel",
    "webtoon"
   ],
   "feeds": [],
   "color": "#8a5a00",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "health-science",
   "group": "life",
   "name": "Health and Science",
   "description": "New research, medical findings, public health and space science.",
   "queries": [
    "(study OR researchers OR scientists) (health OR medicine OR disease)",
    "(NASA OR telescope OR space) discovery"
   ],
   "require": [
    [
     "study",
     "researchers",
     "scientists",
     "research",
     "trial",
     "FDA",
     "NIH",
     "CDC",
     "NASA",
     "discovery",
     "vaccine",
     "disease",
     "medicine",
     "health"
    ]
   ],
   "exclude": [
    "sponsored content",
    "supplement deal"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#0f6e5c",
   "needs_location": false
  },
  {
   "id": "travel",
   "group": "life",
   "name": "Travel",
   "description": "Airlines, airports, cruises, national parks, passports and travel advisories.",
   "queries": [
    "(airlines OR airports OR TSA OR \"national parks\") travelers",
    "(cruise OR \"travel advisory\" OR passport) travelers"
   ],
   "require": [
    [
     "airline",
     "airlines",
     "airport",
     "airports",
     "TSA",
     "flight",
     "flights",
     "travel",
     "travelers",
     "cruise",
     "cruises",
     "national park",
     "national parks",
     "passport",
     "hotel",
     "hotels"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "skip_listicles": true,
   "feeds": [],
   "color": "#7a2f5f",
   "needs_location": false
  }
 ],
 "packs": [
  {
   "id": "starter",
   "name": "A little of everything",
   "description": "Markets, science, travel, AI tools, an inspiring story and your town.",
   "categories": [
    "markets-economy",
    "health-science",
    "travel",
    "ai-tools",
    "inspiring",
    "local-news"
   ]
  },
  {
   "id": "tech-pro",
   "name": "Technology professional",
   "description": "Security, networks, cloud, AI and developer news, plus career skills.",
   "categories": [
    "cybersecurity",
    "network-security",
    "cloud-infrastructure",
    "enterprise-ai",
    "ai-tools",
    "open-source",
    "career-skills"
   ]
  },
  {
   "id": "money",
   "name": "Money and markets",
   "description": "Personal finance, retirement rules, markets and housing.",
   "categories": [
    "personal-finance",
    "retirement-planning",
    "markets-economy",
    "housing"
   ]
  },
  {
   "id": "around-town",
   "name": "Around town",
   "description": "Your community, local government, weather and safety, plus good news and science.",
   "categories": [
    "local-news",
    "local-government",
    "local-weather",
    "inspiring",
    "health-science"
   ]
  },
  {
   "id": "federal-it",
   "name": "Federal IT professional",
   "description": "Ten desks for a federal IT professional: defense AI, workforce actions, the IT industry, corporate AI, AI tools, inspiring stories, pay and leave, retirement, your community, and network security.",
   "categories": [
    "defense-ai",
    "federal-workforce",
    "cybersecurity",
    "enterprise-ai",
    "ai-tools",
    "inspiring",
    "federal-pay",
    "federal-retirement",
    "local-news",
    "network-security"
   ]
  }
 ]
};
