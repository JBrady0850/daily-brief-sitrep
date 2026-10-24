/* Daily Brief category library. Plain JSON after the equals sign, so the app
   reads it in any browser (including file://) and the Python tools read the
   same file. Edit here; see docs/CATEGORIES.md. */
window.DB_LIBRARY = {
 "version": 1,
 "groups": [
  {
   "id": "news",
   "name": "Top news"
  },
  {
   "id": "weather",
   "name": "Weather"
  },
  {
   "id": "sports",
   "name": "Sports"
  },
  {
   "id": "tech",
   "name": "Technology"
  },
  {
   "id": "money",
   "name": "Money and business"
  },
  {
   "id": "science",
   "name": "Science and health"
  },
  {
   "id": "culture",
   "name": "Entertainment and culture"
  },
  {
   "id": "life",
   "name": "Life and home"
  },
  {
   "id": "local",
   "name": "Your area"
  },
  {
   "id": "gov",
   "name": "Government and defense"
  },
  {
   "id": "career",
   "name": "Career and education"
  }
 ],
 "categories": [
  {
   "id": "us-news",
   "group": "news",
   "name": "U.S. Headlines",
   "description": "The biggest national stories of the day, from courts and Congress to disasters and the economy.",
   "queries": [
    "(Congress OR \"Supreme Court\" OR \"White House\" OR governor) (ruling OR vote OR announces OR order)",
    "(nationwide OR \"across the country\" OR federal) (report OR investigation OR announces)"
   ],
   "require": [],
   "exclude": [
    "opinion:",
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml"
   ],
   "color": "#1f3a5f",
   "icon": "flag",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "world-news",
   "group": "news",
   "name": "World News",
   "description": "International news: conflicts, diplomacy, elections abroad and global events.",
   "queries": [
    "(\"United Nations\" OR NATO OR diplomats OR summit OR ceasefire) (talks OR agreement OR leaders)",
    "(Europe OR Asia OR \"Middle East\" OR Africa OR \"Latin America\") (government OR election OR conflict OR crisis)"
   ],
   "require": [],
   "exclude": [
    "opinion:"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://moxie.foxnews.com/google-publisher/world.xml"
   ],
   "color": "#0b5e8f",
   "icon": "globe",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "politics",
   "group": "news",
   "name": "Politics and Policy",
   "description": "Campaigns, Congress, the White House and the policy fights that shape them.",
   "queries": [
    "(Congress OR Senate OR House OR \"White House\") (bill OR vote OR policy OR hearing)",
    "(election OR campaign OR candidates OR polling) (voters OR primary OR race)"
   ],
   "require": [
    [
     "Congress",
     "Senate",
     "House",
     "White House",
     "president",
     "lawmakers",
     "bill",
     "vote",
     "election",
     "campaign",
     "governor",
     "policy",
     "Republicans",
     "Democrats",
     "GOP",
     "candidate",
     "candidates",
     "poll",
     "polls",
     "Supreme Court"
    ]
   ],
   "exclude": [
    "opinion:",
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://moxie.foxnews.com/google-publisher/politics.xml"
   ],
   "color": "#7a1f2b",
   "icon": "capitol",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "business-news",
   "group": "news",
   "name": "Business Headlines",
   "description": "Company news, earnings, deals, layoffs and the business stories everyone is talking about.",
   "queries": [
    "(earnings OR merger OR acquisition OR layoffs OR CEO) (company OR shares OR deal)",
    "(retailers OR automakers OR airlines OR banks OR \"tech giants\") (sales OR profit OR outlook)"
   ],
   "require": [
    [
     "earnings",
     "merger",
     "acquisition",
     "acquire",
     "deal",
     "layoffs",
     "CEO",
     "company",
     "companies",
     "shares",
     "profit",
     "revenue",
     "sales",
     "IPO",
     "bankruptcy",
     "retailer",
     "retailers",
     "business",
     "outlook"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
   ],
   "color": "#0f6e5c",
   "icon": "briefcase",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "good-news",
   "group": "news",
   "name": "Good News",
   "description": "Uplifting stories: rescues, kindness, community wins and breakthroughs that went right.",
   "queries": [
    "(\"good news\" OR heartwarming OR uplifting OR kindness) (community OR rescued OR donated OR volunteers)",
    "(rescued OR reunited OR \"pays it forward\" OR donates) (family OR community OR neighbors)"
   ],
   "require": [
    [
     "good news",
     "heartwarming",
     "uplifting",
     "kindness",
     "kind",
     "rescued",
     "rescue",
     "reunited",
     "donated",
     "donates",
     "volunteer",
     "volunteers",
     "celebrates",
     "hero",
     "heroes",
     "generous",
     "gift",
     "inspiring"
    ]
   ],
   "exclude": [
    "obituary",
    "shooting",
    "killed",
    "crash",
    "lawsuit",
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml"
   ],
   "topic_feeds": [
    "https://moxie.foxnews.com/google-publisher/good-news.xml"
   ],
   "color": "#a06527",
   "icon": "star",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "local-weather",
   "group": "weather",
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
   "exclude": [
    "arrested",
    "arrest",
    "charged",
    "sentenced",
    "homicide"
   ],
   "feeds": [],
   "color": "#34495e",
   "needs_location": true,
   "skip_listicles": false,
   "icon": "umbrella"
  },
  {
   "id": "severe-weather",
   "group": "weather",
   "name": "Severe Weather Across the Country",
   "description": "Hurricanes, tornadoes, winter storms, heat waves, floods and wildfires anywhere in the country.",
   "queries": [
    "(hurricane OR tornado OR blizzard OR \"winter storm\" OR \"heat wave\" OR \"severe storms\") (warning OR forecast OR \"National Weather Service\")",
    "(\"tropical storm\" OR flooding OR wildfire OR \"extreme heat\" OR \"ice storm\") (evacuation OR warning OR forecast)"
   ],
   "require": [
    [
     "hurricane",
     "tornado",
     "tornadoes",
     "blizzard",
     "winter storm",
     "snowstorm",
     "heat wave",
     "extreme heat",
     "severe storms",
     "severe weather",
     "tropical storm",
     "flood",
     "flooding",
     "wildfire",
     "wildfires",
     "forecast",
     "National Weather Service",
     "storm",
     "storms",
     "ice storm",
     "weather"
    ]
   ],
   "exclude": [
    "Carolina Hurricanes",
    "Miami Heat",
    "Tampa Bay Lightning",
    "Oklahoma City Thunder",
    "perfect storm",
    "storm of criticism",
    "brainstorm",
    "Storm Area",
    "Seattle Storm"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Weather.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml"
   ],
   "color": "#2b6cc4",
   "icon": "alert",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "weather-outlook",
   "group": "weather",
   "name": "Forecasts and Seasonal Outlook",
   "description": "The big picture: seasonal outlooks, El Nino and La Nina, first frost, pollen and hurricane season.",
   "queries": [
    "(NOAA OR \"Climate Prediction Center\" OR \"National Weather Service\") (outlook OR forecast OR season)",
    "(\"El Nino\" OR \"La Nina\" OR \"winter outlook\" OR \"hurricane season\" OR \"first frost\" OR pollen) forecast"
   ],
   "require": [
    [
     "outlook",
     "forecast",
     "forecasters",
     "El Nino",
     "La Nina",
     "NOAA",
     "season",
     "seasonal",
     "winter",
     "summer",
     "hurricane season",
     "frost",
     "pollen",
     "meteorologist",
     "meteorologists"
    ]
   ],
   "exclude": [
    "Carolina Hurricanes",
    "earnings outlook",
    "economic outlook",
    "market outlook"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Weather.xml"
   ],
   "color": "#3673c8",
   "icon": "sun",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "climate-environment",
   "group": "weather",
   "name": "Climate and Environment",
   "description": "Climate science, extreme weather trends, conservation, energy transition and environmental rules.",
   "queries": [
    "(climate OR \"global warming\" OR emissions OR conservation) (study OR scientists OR report OR policy)",
    "(EPA OR environmental OR wildlife OR \"clean energy\") (rule OR report OR protection OR study)"
   ],
   "require": [
    [
     "climate",
     "global warming",
     "emissions",
     "carbon",
     "conservation",
     "environment",
     "environmental",
     "EPA",
     "wildlife",
     "pollution",
     "clean energy",
     "renewable",
     "drought",
     "sea level",
     "endangered"
    ]
   ],
   "exclude": [
    "climate of fear",
    "political climate",
    "business climate",
    "economic climate"
   ],
   "feeds": [
    "https://www.utilitydive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml"
   ],
   "color": "#2e7d4f",
   "icon": "leaf",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "sports-headlines",
   "group": "sports",
   "name": "Sports Headlines",
   "description": "The top stories across every major sport: scores, trades, injuries and big moments.",
   "queries": [
    "(NFL OR NBA OR MLB OR NHL OR \"college football\") (wins OR beats OR trade OR injury)",
    "(championship OR playoffs OR \"World Series\" OR \"Super Bowl\" OR \"Stanley Cup\") (game OR series OR team)"
   ],
   "require": [],
   "exclude": [
    "betting odds",
    "best bets",
    "prediction",
    "picks against the spread",
    "sportsbook",
    "promo code"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/news",
    "https://www.cbssports.com/rss/headlines/"
   ],
   "color": "#c0392b",
   "icon": "trophy",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "nfl",
   "group": "sports",
   "name": "NFL Football",
   "description": "Pro football: games, trades, injuries, coaching moves and the playoff race.",
   "queries": [
    "NFL (quarterback OR touchdown OR trade OR injury OR coach)",
    "(NFL OR \"Super Bowl\") (playoffs OR standings OR \"game recap\" OR roster)"
   ],
   "require": [
    [
     "NFL",
     "quarterback",
     "touchdown",
     "Super Bowl",
     "wide receiver",
     "linebacker",
     "head coach",
     "Cardinals",
     "Falcons",
     "Ravens",
     "Bills",
     "Panthers",
     "Bears",
     "Bengals",
     "Browns",
     "Cowboys",
     "Broncos",
     "Lions",
     "Packers",
     "Texans",
     "Colts",
     "Jaguars",
     "Chiefs",
     "Raiders",
     "Chargers",
     "Rams",
     "Dolphins",
     "Vikings",
     "Patriots",
     "Saints",
     "Giants",
     "Jets",
     "Eagles",
     "Steelers",
     "49ers",
     "Seahawks",
     "Buccaneers",
     "Titans",
     "Commanders"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "picks against the spread",
    "sportsbook",
    "promo code",
    "fantasy football"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/nfl/news",
    "https://www.cbssports.com/rss/headlines/nfl/"
   ],
   "color": "#013369",
   "icon": "football",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "college-football",
   "group": "sports",
   "name": "College Football",
   "description": "Rankings, rivalry games, the playoff picture, recruiting and coaching changes.",
   "queries": [
    "\"college football\" (rankings OR playoff OR Heisman OR upset OR coach)",
    "(SEC OR \"Big Ten\" OR ACC OR \"Big 12\") football (game OR ranking OR coach)"
   ],
   "require": [
    [
     "college football",
     "CFP",
     "College Football Playoff",
     "Heisman",
     "SEC",
     "Big Ten",
     "ACC",
     "Big 12",
     "bowl",
     "recruiting",
     "Alabama",
     "Georgia",
     "Ohio State",
     "Michigan",
     "Texas",
     "LSU",
     "Clemson",
     "Notre Dame",
     "Oregon",
     "Penn State",
     "Florida State",
     "Tennessee",
     "Oklahoma",
     "Miami",
     "USC",
     "Auburn",
     "Florida"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "picks against the spread",
    "sportsbook",
    "promo code",
    "basketball"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/ncf/news",
    "https://www.cbssports.com/rss/headlines/college-football/"
   ],
   "color": "#9e1b32",
   "icon": "college",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "nba",
   "group": "sports",
   "name": "NBA Basketball",
   "description": "Pro basketball: games, trades, injuries, standings and the playoff race.",
   "queries": [
    "NBA (trade OR injury OR \"triple-double\" OR coach OR playoffs)",
    "(NBA OR basketball) (Lakers OR Celtics OR Knicks OR Warriors OR Bucks OR Nuggets)"
   ],
   "require": [
    [
     "NBA",
     "basketball",
     "point guard",
     "triple-double",
     "playoffs",
     "Hawks",
     "Celtics",
     "Nets",
     "Hornets",
     "Bulls",
     "Cavaliers",
     "Mavericks",
     "Nuggets",
     "Pistons",
     "Warriors",
     "Rockets",
     "Pacers",
     "Clippers",
     "Lakers",
     "Grizzlies",
     "Miami Heat",
     "Bucks",
     "Timberwolves",
     "Pelicans",
     "Knicks",
     "Thunder",
     "Orlando Magic",
     "76ers",
     "Suns",
     "Trail Blazers",
     "Sacramento Kings",
     "Spurs",
     "Raptors",
     "Utah Jazz",
     "Wizards"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "WNBA",
    "college basketball"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/nba/news",
    "https://www.cbssports.com/rss/headlines/nba/"
   ],
   "color": "#c9082a",
   "icon": "basketball",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "college-basketball",
   "group": "sports",
   "name": "College Basketball",
   "description": "Men's and women's college hoops: rankings, upsets, conference races and March Madness.",
   "queries": [
    "\"college basketball\" (rankings OR upset OR tournament OR coach)",
    "(\"March Madness\" OR \"NCAA tournament\" OR \"Final Four\" OR \"AP Top 25\") basketball"
   ],
   "require": [
    [
     "college basketball",
     "March Madness",
     "NCAA tournament",
     "Final Four",
     "AP Top 25",
     "men's basketball",
     "women's basketball",
     "Duke",
     "Kentucky",
     "Kansas",
     "UConn",
     "North Carolina",
     "Gonzaga",
     "Big East"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "football"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/ncb/news"
   ],
   "color": "#b25d1b",
   "icon": "basketball",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "mlb",
   "group": "sports",
   "name": "MLB Baseball",
   "description": "Major League Baseball: games, trades, free agency, injuries and the pennant races.",
   "queries": [
    "MLB (trade OR \"free agent\" OR injury OR \"home run\" OR manager)",
    "(MLB OR baseball) (\"World Series\" OR playoffs OR postseason OR \"spring training\")"
   ],
   "require": [
    [
     "MLB",
     "baseball",
     "home run",
     "pitcher",
     "World Series",
     "free agent",
     "spring training",
     "postseason",
     "Diamondbacks",
     "Braves",
     "Orioles",
     "Red Sox",
     "Cubs",
     "White Sox",
     "Reds",
     "Guardians",
     "Rockies",
     "Tigers",
     "Astros",
     "Royals",
     "Angels",
     "Dodgers",
     "Marlins",
     "Brewers",
     "Twins",
     "Mets",
     "Yankees",
     "Athletics",
     "Phillies",
     "Pirates",
     "Padres",
     "Mariners",
     "Rays",
     "Blue Jays",
     "Nationals"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "college baseball"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/mlb/news",
    "https://www.cbssports.com/rss/headlines/mlb/"
   ],
   "color": "#002d72",
   "icon": "baseball",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "nhl",
   "group": "sports",
   "name": "NHL Hockey",
   "description": "Pro hockey: games, trades, injuries, standings and the Stanley Cup chase.",
   "queries": [
    "NHL (trade OR injury OR goalie OR coach OR playoffs)",
    "(NHL OR hockey) (\"Stanley Cup\" OR standings OR \"power play\" OR overtime)"
   ],
   "require": [
    [
     "NHL",
     "hockey",
     "Stanley Cup",
     "goalie",
     "power play",
     "hat trick",
     "Ducks",
     "Bruins",
     "Sabres",
     "Flames",
     "Hurricanes",
     "Blackhawks",
     "Avalanche",
     "Blue Jackets",
     "Dallas Stars",
     "Red Wings",
     "Oilers",
     "Florida Panthers",
     "LA Kings",
     "Minnesota Wild",
     "Canadiens",
     "Predators",
     "Devils",
     "Islanders",
     "Rangers",
     "Senators",
     "Flyers",
     "Penguins",
     "Sharks",
     "Kraken",
     "St. Louis Blues",
     "Lightning",
     "Maple Leafs",
     "Canucks",
     "Golden Knights",
     "Capitals",
     "Winnipeg Jets",
     "Mammoth"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "field hockey",
    "college hockey"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/nhl/news",
    "https://www.cbssports.com/rss/headlines/nhl/"
   ],
   "color": "#111111",
   "icon": "hockey",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "soccer",
   "group": "sports",
   "name": "Soccer",
   "description": "MLS, the Premier League, the Champions League, the national teams and the World Cup.",
   "queries": [
    "(MLS OR \"Premier League\" OR \"Champions League\" OR \"La Liga\") (match OR transfer OR goal OR manager)",
    "(USMNT OR USWNT OR NWSL OR FIFA OR \"World Cup\") (match OR roster OR coach OR qualifying)"
   ],
   "require": [
    [
     "soccer",
     "MLS",
     "Premier League",
     "Champions League",
     "La Liga",
     "Bundesliga",
     "Serie A",
     "USMNT",
     "USWNT",
     "NWSL",
     "FIFA",
     "World Cup",
     "midfielder",
     "striker",
     "goalkeeper",
     "transfer"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "fantasy"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.cbssports.com/rss/headlines/soccer/"
   ],
   "color": "#1b7a3e",
   "icon": "soccer",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "golf",
   "group": "sports",
   "name": "Golf",
   "description": "The PGA Tour, LPGA, LIV and the majors: leaderboards, winners and big moves.",
   "queries": [
    "(PGA OR LPGA OR \"PGA Tour\" OR LIV) (leaderboard OR wins OR tournament OR round)",
    "(Masters OR \"U.S. Open\" OR \"Ryder Cup\" OR \"British Open\") golf"
   ],
   "require": [
    [
     "golf",
     "PGA",
     "LPGA",
     "LIV",
     "Masters",
     "Ryder Cup",
     "U.S. Open",
     "Open Championship",
     "birdie",
     "leaderboard"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "mini golf",
    "golf cart"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/golf/news",
    "https://www.cbssports.com/rss/headlines/golf/"
   ],
   "color": "#2e6b30",
   "icon": "golf",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "motorsports",
   "group": "sports",
   "name": "Motorsports",
   "description": "NASCAR, Formula 1 and IndyCar: race results, standings and driver news.",
   "queries": [
    "(NASCAR OR \"Formula 1\" OR IndyCar) (race OR qualifying OR driver OR championship)",
    "(\"Grand Prix\" OR \"Cup Series\" OR \"Indy 500\" OR Daytona) (race OR driver OR wins)"
   ],
   "require": [
    [
     "NASCAR",
     "Formula 1",
     "F1",
     "IndyCar",
     "Grand Prix",
     "Cup Series",
     "Indy 500",
     "Daytona",
     "race",
     "driver"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "horse race",
    "arms race",
    "race for"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/rpm/news"
   ],
   "color": "#c64e00",
   "icon": "racing",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "tennis",
   "group": "sports",
   "name": "Tennis",
   "description": "The ATP and WTA tours and the four Grand Slams.",
   "queries": [
    "(ATP OR WTA OR tennis) (match OR wins OR upset OR final)",
    "(Wimbledon OR \"US Open\" OR \"Australian Open\" OR \"French Open\" OR \"Roland Garros\") tennis"
   ],
   "require": [
    [
     "tennis",
     "ATP",
     "WTA",
     "Wimbledon",
     "US Open",
     "Australian Open",
     "French Open",
     "Roland Garros",
     "Grand Slam"
    ]
   ],
   "exclude": [
    "betting odds",
    "best bets",
    "sportsbook",
    "promo code",
    "table tennis"
   ],
   "feeds": [],
   "topic_feeds": [
    "https://www.espn.com/espn/rss/tennis/news",
    "https://rss.nytimes.com/services/xml/rss/nyt/Tennis.xml"
   ],
   "color": "#617c1a",
   "icon": "tennis",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "fantasy-sports",
   "group": "sports",
   "name": "Fantasy Football and Sports",
   "description": "Waiver wire pickups, start and sit calls, injury updates and rankings for fantasy players.",
   "queries": [
    "\"fantasy football\" (waiver OR rankings OR start OR sit OR sleepers)",
    "(fantasy OR \"fantasy football\" OR \"fantasy basketball\") (injury OR waiver OR rankings)"
   ],
   "require": [
    [
     "fantasy"
    ]
   ],
   "exclude": [
    "fantasy novel",
    "fantasy film",
    "fantasy series",
    "final fantasy",
    "sportsbook",
    "promo code"
   ],
   "feeds": [
    "https://www.espn.com/espn/rss/nfl/news",
    "https://www.cbssports.com/rss/headlines/nfl/"
   ],
   "topic_feeds": [
    "https://www.espn.com/espn/rss/fantasy/news"
   ],
   "color": "#6c3483",
   "icon": "chart",
   "skip_listicles": false,
   "needs_location": false
  },
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
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.wired.com/feed/category/security/latest/rss",
    "https://www.cybersecuritydive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://www.darkreading.com/rss.xml"
   ],
   "color": "#1f3a5f",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "lock"
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
   "feeds": [
    "https://www.wired.com/feed/category/security/latest/rss",
    "https://www.darkreading.com/rss.xml",
    "https://www.ciodive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://www.cybersecuritydive.com/feeds/news/"
   ],
   "color": "#34495e",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "network"
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    "https://www.ciodive.com/feeds/news/",
    "https://www.utilitydive.com/feeds/news/",
    "https://www.constructiondive.com/feeds/news/"
   ],
   "color": "#0b5e8f",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "cloud"
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    "https://www.wired.com/feed/tag/ai/latest/rss"
   ],
   "color": "#5b3485",
   "needs_location": false,
   "icon": "chip"
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
   "feeds": [
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://moxie.foxnews.com/google-publisher/tech.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/PersonalTech.xml",
    "https://www.ciodive.com/feeds/news/"
   ],
   "color": "#a04000",
   "needs_location": false,
   "icon": "sparkle"
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
   "feeds": [
    "https://www.wired.com/feed/rss",
    "https://www.ciodive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://github.blog/feed/"
   ],
   "color": "#1b6e3d",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "code"
  },
  {
   "id": "tech-news",
   "group": "tech",
   "name": "Technology Headlines",
   "description": "The big tech stories: Apple, Google, Microsoft, Amazon and Meta, new products and tech policy.",
   "queries": [
    "(Apple OR Google OR Microsoft OR Amazon OR Meta OR Nvidia) (launch OR announces OR lawsuit OR antitrust)",
    "(smartphone OR \"artificial intelligence\" OR chips OR software) (company OR launch OR announces)"
   ],
   "require": [
    [
     "Apple",
     "Google",
     "Microsoft",
     "Amazon",
     "Meta",
     "Nvidia",
     "Tesla",
     "OpenAI",
     "Anthropic",
     "tech",
     "technology",
     "smartphone",
     "iPhone",
     "Android",
     "chip",
     "chips",
     "software",
     "app",
     "apps",
     "AI",
     "artificial intelligence"
    ]
   ],
   "exclude": [
    "sponsored content",
    "deal of the day",
    "promo code",
    "coupon"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.wired.com/feed/rss",
    "https://moxie.foxnews.com/google-publisher/tech.xml",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html"
   ],
   "color": "#34495e",
   "icon": "phone",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "gadgets",
   "group": "tech",
   "name": "Gadgets and Reviews",
   "description": "New phones, laptops, wearables and smart home gear, with launches and hands-on reviews.",
   "queries": [
    "(iPhone OR Pixel OR Galaxy OR laptop OR smartwatch OR earbuds) (review OR launch OR announced)",
    "(\"smart home\" OR headphones OR tablet OR \"gaming PC\") (review OR launch OR release)"
   ],
   "require": [
    [
     "iPhone",
     "Pixel",
     "Galaxy",
     "laptop",
     "laptops",
     "smartwatch",
     "watch",
     "earbuds",
     "headphones",
     "tablet",
     "iPad",
     "smart home",
     "camera",
     "phone",
     "gadget",
     "gadgets",
     "review"
    ]
   ],
   "exclude": [
    "deal of the day",
    "promo code",
    "coupon",
    "Black Friday deal",
    "sponsored content"
   ],
   "feeds": [
    "https://www.wired.com/feed/category/gear/latest/rss"
   ],
   "color": "#5d6d7e",
   "icon": "phone",
   "skip_listicles": true,
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
   "feeds": [
    "https://www.cnbc.com/id/21324812/device/rss/rss.html",
    "https://www.bankingdive.com/feeds/news/",
    "https://www.cnbc.com/id/10001054/device/rss/rss.html"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/YourMoney.xml"
   ],
   "color": "#1d6aa0",
   "needs_location": false,
   "icon": "coin"
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/YourMoney.xml",
    "https://www.cnbc.com/id/10001054/device/rss/rss.html",
    "https://www.cnbc.com/id/21324812/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"
   ],
   "color": "#922b21",
   "needs_location": false,
   "icon": "hourglass"
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
   "feeds": [
    "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
   ],
   "color": "#0f6e5c",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "chart"
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
   "feeds": [
    "https://www.cnbc.com/id/10000115/device/rss/rss.html",
    "https://www.constructiondive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/RealEstate.xml"
   ],
   "color": "#6b4f2a",
   "needs_location": false,
   "icon": "house"
  },
  {
   "id": "small-business",
   "group": "money",
   "name": "Small Business",
   "description": "Help for owners: loans, taxes, hiring, SBA programs and the economy for Main Street.",
   "queries": [
    "\"small business\" (owners OR loans OR SBA OR taxes OR hiring)",
    "(\"small businesses\" OR entrepreneurs OR \"Main Street\") (survey OR rule OR program OR economy)"
   ],
   "require": [
    [
     "small business",
     "small businesses",
     "SBA",
     "entrepreneur",
     "entrepreneurs",
     "owners",
     "Main Street",
     "startup",
     "startups"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.retaildive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/SmallBusiness.xml",
    "https://www.cnbc.com/id/44877279/device/rss/rss.html"
   ],
   "color": "#12836d",
   "icon": "cart",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "crypto",
   "group": "money",
   "name": "Crypto and Digital Assets",
   "description": "Bitcoin and other digital assets: prices, regulation, ETFs and major hacks.",
   "queries": [
    "(bitcoin OR ethereum OR crypto OR cryptocurrency) (price OR SEC OR ETF OR regulation)",
    "(stablecoin OR blockchain OR \"crypto exchange\") (rule OR hack OR launch OR lawsuit)"
   ],
   "require": [
    [
     "bitcoin",
     "ethereum",
     "crypto",
     "cryptocurrency",
     "stablecoin",
     "blockchain",
     "digital assets",
     "Coinbase",
     "ETF"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "airdrop",
    "price prediction"
   ],
   "feeds": [
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.paymentsdive.com/feeds/news/",
    "https://www.bankingdive.com/feeds/news/",
    "https://www.cnbc.com/id/15839069/device/rss/rss.html",
    "https://moxie.foxnews.com/google-publisher/tech.xml"
   ],
   "color": "#a2680c",
   "icon": "crypto",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "energy",
   "group": "money",
   "name": "Energy and Gas Prices",
   "description": "Gas and oil prices, electric bills, power grids and the energy industry.",
   "queries": [
    "(\"gas prices\" OR \"oil prices\" OR OPEC OR crude) (price OR drivers OR output)",
    "(\"electricity prices\" OR \"power grid\" OR utility OR \"natural gas\") (rates OR bills OR outage OR demand)"
   ],
   "require": [
    [
     "gas prices",
     "gasoline",
     "oil",
     "crude",
     "OPEC",
     "electricity",
     "power grid",
     "grid",
     "utility",
     "utilities",
     "natural gas",
     "energy",
     "solar",
     "nuclear",
     "pipeline"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Climate.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html"
   ],
   "color": "#946f10",
   "icon": "bolt",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "health-science",
   "group": "science",
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml"
   ],
   "color": "#0f6e5c",
   "needs_location": false,
   "icon": "health"
  },
  {
   "id": "space",
   "group": "science",
   "name": "Space and Astronomy",
   "description": "NASA missions, rocket launches, telescopes, the Moon and Mars, and sky events to watch.",
   "queries": [
    "(NASA OR SpaceX OR \"Blue Origin\" OR rocket) (launch OR mission OR astronauts OR Moon OR Mars)",
    "(telescope OR astronomers OR asteroid OR comet OR eclipse OR meteor) (discovery OR spotted OR study)"
   ],
   "require": [
    [
     "NASA",
     "SpaceX",
     "Blue Origin",
     "rocket",
     "launch",
     "astronaut",
     "astronauts",
     "Moon",
     "lunar",
     "Mars",
     "telescope",
     "astronomers",
     "asteroid",
     "comet",
     "eclipse",
     "meteor",
     "space",
     "galaxy",
     "planet",
     "satellite"
    ]
   ],
   "exclude": [
    "space heater",
    "office space",
    "parking space",
    "safe space",
    "spaceship earth"
   ],
   "feeds": [
    "https://www.nasa.gov/news-release/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Space.xml"
   ],
   "color": "#1a237e",
   "icon": "rocket",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "science-discovery",
   "group": "science",
   "name": "Science and Discovery",
   "description": "New findings across physics, biology, archaeology and the natural world.",
   "queries": [
    "(scientists OR researchers OR study) (discovery OR discovered OR finds OR breakthrough)",
    "(fossil OR archaeologists OR species OR physicists OR \"new study\") (discovery OR found OR reveals)"
   ],
   "require": [
    [
     "scientists",
     "researchers",
     "study",
     "discovery",
     "discovered",
     "fossil",
     "archaeologists",
     "species",
     "physicists",
     "breakthrough",
     "experiment",
     "evolution",
     "dinosaur",
     "ancient"
    ]
   ],
   "exclude": [
    "sponsored content",
    "case study"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    "https://www.wired.com/feed/category/science/latest/rss"
   ],
   "color": "#00796b",
   "icon": "flask",
   "skip_listicles": false,
   "needs_location": false
  },
  {
   "id": "health-wellness",
   "group": "science",
   "name": "Health and Wellness",
   "description": "Everyday health: nutrition, fitness, sleep, mental health and new medical guidance.",
   "queries": [
    "(health OR wellness OR nutrition OR fitness OR sleep) (study OR doctors OR guidance OR tips)",
    "(\"mental health\" OR \"heart health\" OR diet OR exercise) (study OR researchers OR experts)"
   ],
   "require": [
    [
     "health",
     "healthy",
     "wellness",
     "nutrition",
     "diet",
     "fitness",
     "exercise",
     "sleep",
     "mental health",
     "heart",
     "doctors",
     "study",
     "vaccine",
     "FDA",
     "CDC",
     "disease",
     "cancer",
     "obesity"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "health insurance stocks"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    "https://moxie.foxnews.com/google-publisher/health.xml"
   ],
   "color": "#c2185b",
   "icon": "health",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "movies",
   "group": "culture",
   "name": "Movies",
   "description": "New releases, box office, awards season, trailers and film industry news.",
   "queries": [
    "(movie OR film) (\"box office\" OR premiere OR trailer OR review OR sequel)",
    "(Oscars OR \"film festival\" OR Hollywood OR studio) (film OR movie OR award)"
   ],
   "require": [
    [
     "movie",
     "movies",
     "film",
     "films",
     "box office",
     "Oscar",
     "Oscars",
     "Hollywood",
     "director",
     "sequel",
     "trailer",
     "premiere",
     "studio",
     "cinema"
    ]
   ],
   "exclude": [
    "sponsored content",
    "streaming deal"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Movies.xml"
   ],
   "color": "#6a1b9a",
   "icon": "film",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "tv-streaming",
   "group": "culture",
   "name": "Television and Streaming",
   "description": "What's new on Netflix, Disney+, Max and the networks: premieres, renewals and cancellations.",
   "queries": [
    "(Netflix OR \"Disney+\" OR Hulu OR \"Prime Video\" OR HBO OR Max) (series OR season OR premiere OR canceled OR renewed)",
    "(television OR \"TV series\" OR sitcom OR \"late-night\") (season OR premiere OR ratings OR finale)"
   ],
   "require": [
    [
     "Netflix",
     "Disney+",
     "Hulu",
     "Prime Video",
     "HBO",
     "Max",
     "Apple TV",
     "Peacock",
     "Paramount+",
     "series",
     "season",
     "episode",
     "premiere",
     "renewed",
     "canceled",
     "television",
     "sitcom",
     "showrunner",
     "streaming"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "stock"
   ],
   "feeds": [
    "https://moxie.foxnews.com/google-publisher/entertainment.xml",
    "https://www.cnbc.com/id/10000110/device/rss/rss.html"
   ],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Television.xml"
   ],
   "color": "#8e24aa",
   "icon": "tv",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "music",
   "group": "culture",
   "name": "Music",
   "description": "New albums, tours, the charts, awards and artist news.",
   "queries": [
    "(album OR single OR tour OR concert) (singer OR band OR rapper OR artist)",
    "(Grammys OR Billboard OR \"music festival\" OR \"Hot 100\") (artist OR album OR song)"
   ],
   "require": [
    [
     "album",
     "single",
     "song",
     "songs",
     "tour",
     "concert",
     "singer",
     "band",
     "rapper",
     "artist",
     "Grammy",
     "Grammys",
     "Billboard",
     "music",
     "festival"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Music.xml"
   ],
   "color": "#ad1457",
   "icon": "music",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "books",
   "group": "culture",
   "name": "Books and Authors",
   "description": "New books, bestsellers, author interviews and literary prizes.",
   "queries": [
    "(book OR novel OR memoir OR author) (bestseller OR release OR prize OR review)",
    "(\"book club\" OR \"best-seller list\" OR \"National Book Award\" OR Pulitzer) (book OR author)"
   ],
   "require": [
    [
     "book",
     "books",
     "novel",
     "memoir",
     "author",
     "authors",
     "bestseller",
     "best-seller",
     "literary",
     "Pulitzer",
     "library",
     "publisher"
    ]
   ],
   "exclude": [
    "sponsored content",
    "Facebook",
    "order book",
    "book value"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml"
   ],
   "color": "#4e342e",
   "icon": "book",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "gaming",
   "group": "culture",
   "name": "Video Games",
   "description": "Game releases, consoles, esports and the gaming industry.",
   "queries": [
    "(\"video game\" OR PlayStation OR Xbox OR Nintendo OR Steam) (release OR launch OR update OR console)",
    "(esports OR \"game studio\" OR \"Game Awards\" OR GTA) (players OR release OR tournament)"
   ],
   "require": [
    [
     "video game",
     "video games",
     "game",
     "games",
     "gaming",
     "PlayStation",
     "Xbox",
     "Nintendo",
     "Switch",
     "Steam",
     "esports",
     "console",
     "gamers"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "game show",
    "football game",
    "basketball game"
   ],
   "feeds": [
    "https://www.wired.com/feed/category/culture/latest/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",
    "https://moxie.foxnews.com/google-publisher/tech.xml",
    "https://moxie.foxnews.com/google-publisher/entertainment.xml"
   ],
   "color": "#283593",
   "icon": "gamepad",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "arts-culture",
   "group": "culture",
   "name": "Arts and Culture",
   "description": "Museums, theater, art, design and the culture stories worth your time.",
   "queries": [
    "(museum OR exhibition OR Broadway OR theater OR gallery) (opens OR show OR artist OR review)",
    "(artist OR painting OR sculpture OR ballet OR opera) (exhibition OR premiere OR auction)"
   ],
   "require": [
    [
     "museum",
     "exhibition",
     "exhibit",
     "Broadway",
     "theater",
     "theatre",
     "gallery",
     "artist",
     "artists",
     "painting",
     "sculpture",
     "ballet",
     "opera",
     "auction",
     "art"
    ]
   ],
   "exclude": [
    "sponsored content",
    "state of the art",
    "martial art"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml"
   ],
   "color": "#795548",
   "icon": "star",
   "skip_listicles": true,
   "needs_location": false
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml",
    "https://moxie.foxnews.com/google-publisher/sports.xml"
   ],
   "topic_feeds": [
    "https://moxie.foxnews.com/google-publisher/good-news.xml"
   ],
   "color": "#8a5a00",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "sunrise"
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Travel.xml",
    "https://moxie.foxnews.com/google-publisher/travel.xml"
   ],
   "color": "#7a2f5f",
   "needs_location": false,
   "icon": "plane"
  },
  {
   "id": "food-dining",
   "group": "life",
   "name": "Food and Dining",
   "description": "Recipes and cooking trends, restaurant news, food prices and recalls.",
   "queries": [
    "(restaurant OR chef OR recipe OR cooking) (new OR opens OR trend OR review)",
    "(\"food prices\" OR \"grocery prices\" OR \"food recall\" OR FDA) (shoppers OR recall OR prices)"
   ],
   "require": [
    [
     "restaurant",
     "restaurants",
     "chef",
     "recipe",
     "recipes",
     "cooking",
     "food",
     "grocery",
     "groceries",
     "dining",
     "menu",
     "recall",
     "baking",
     "wine",
     "coffee"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "food stamps"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/DiningandWine.xml"
   ],
   "color": "#bf360c",
   "icon": "food",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "autos",
   "group": "life",
   "name": "Cars and Electric Vehicles",
   "description": "New models, recalls, gas and electric cars, prices and the auto industry.",
   "queries": [
    "(automakers OR Ford OR Toyota OR GM OR Tesla OR Honda) (recall OR model OR prices OR sales)",
    "(\"electric vehicle\" OR \"electric vehicles\" OR hybrid OR \"car prices\") (buyers OR sales OR charging OR recall)"
   ],
   "require": [
    [
     "car",
     "cars",
     "auto",
     "automaker",
     "automakers",
     "vehicle",
     "vehicles",
     "electric vehicle",
     "electric vehicles",
     "hybrid",
     "Ford",
     "Toyota",
     "GM",
     "Tesla",
     "Honda",
     "Hyundai",
     "recall",
     "truck",
     "SUV"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "car crash",
    "car accident"
   ],
   "feeds": [],
   "topic_feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Automobiles.xml",
    "https://www.cnbc.com/id/10000101/device/rss/rss.html"
   ],
   "color": "#37474f",
   "icon": "car",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "home-garden",
   "group": "life",
   "name": "Home and Garden",
   "description": "Home improvement, gardening, cleaning, energy savings and household safety recalls.",
   "queries": [
    "(\"home improvement\" OR renovation OR gardening OR garden) (tips OR trend OR experts OR season)",
    "(\"Consumer Product Safety Commission\" OR recall) (furniture OR appliance OR household OR product)"
   ],
   "require": [
    [
     "home improvement",
     "renovation",
     "remodel",
     "garden",
     "gardening",
     "lawn",
     "plants",
     "kitchen",
     "appliance",
     "appliances",
     "furniture",
     "household",
     "recall",
     "homeowners"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "nursing home",
    "home run",
    "home game"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/RealEstate.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml",
    "https://www.constructiondive.com/feeds/news/",
    "https://www.retaildive.com/feeds/news/"
   ],
   "color": "#4f822c",
   "icon": "house",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "pets",
   "group": "life",
   "name": "Pets and Animals",
   "description": "Pet health, adoption, recalls of pet food and amazing animal stories.",
   "queries": [
    "(pets OR dogs OR cats OR \"pet food\") (veterinarians OR recall OR adoption OR health)",
    "(animal OR wildlife OR shelter OR zoo) (rescue OR adopted OR born OR rescued)"
   ],
   "require": [
    [
     "pet",
     "pets",
     "dog",
     "dogs",
     "puppy",
     "cat",
     "cats",
     "kitten",
     "pet food",
     "veterinarian",
     "veterinarians",
     "vet",
     "adoption",
     "shelter",
     "animal",
     "animals",
     "zoo",
     "wildlife"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code",
    "hot dog",
    "top dog",
    "Cats musical"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml"
   ],
   "color": "#8d6e63",
   "icon": "paw",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "parenting-family",
   "group": "life",
   "name": "Parenting and Family",
   "description": "Raising kids: schools, child health, screen time, child care costs and family life.",
   "queries": [
    "(parents OR parenting OR kids OR children) (study OR tips OR schools OR experts)",
    "(\"child care\" OR \"screen time\" OR pediatricians OR teens) (parents OR study OR costs)"
   ],
   "require": [
    [
     "parents",
     "parenting",
     "kids",
     "children",
     "child",
     "child care",
     "childcare",
     "teens",
     "teenagers",
     "pediatricians",
     "screen time",
     "toddlers",
     "babies",
     "family",
     "families"
    ]
   ],
   "exclude": [
    "sponsored content",
    "parent company"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Education.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml",
    "https://moxie.foxnews.com/google-publisher/health.xml"
   ],
   "color": "#bc5500",
   "icon": "people",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "outdoors",
   "group": "life",
   "name": "Outdoors and National Parks",
   "description": "National and state parks, hiking, camping, fishing and hunting seasons.",
   "queries": [
    "(\"national park\" OR \"state park\" OR hiking OR camping) (visitors OR trail OR reopens OR closure)",
    "(fishing OR hunting OR \"wildlife officials\") (season OR rules OR license)"
   ],
   "require": [
    [
     "national park",
     "national parks",
     "state park",
     "hiking",
     "hikers",
     "trail",
     "trails",
     "camping",
     "campground",
     "fishing",
     "hunting",
     "outdoors",
     "wildlife"
    ]
   ],
   "exclude": [
    "sponsored content",
    "promo code"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Travel.xml",
    "https://moxie.foxnews.com/google-publisher/travel.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://moxie.foxnews.com/google-publisher/lifestyle.xml"
   ],
   "color": "#33691e",
   "icon": "mountain",
   "skip_listicles": true,
   "needs_location": false
  },
  {
   "id": "faith-religion",
   "group": "life",
   "name": "Faith and Religion",
   "description": "News from churches, synagogues, mosques and faith communities, and religion in public life.",
   "queries": [
    "(church OR churches OR pastor OR pope OR synagogue OR mosque) (community OR congregation OR leaders)",
    "(faith OR religious OR religion) (leaders OR community OR survey OR freedom)"
   ],
   "require": [
    [
     "church",
     "churches",
     "pastor",
     "pope",
     "Vatican",
     "synagogue",
     "mosque",
     "faith",
     "religious",
     "religion",
     "congregation",
     "worship",
     "bishop",
     "ministry"
    ]
   ],
   "exclude": [
    "sponsored content"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://moxie.foxnews.com/google-publisher/world.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
   ],
   "color": "#5d4037",
   "icon": "sunrise",
   "skip_listicles": false,
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
   "skip_listicles": false,
   "icon": "pin"
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
     "commissioner",
     "budget",
     "ordinance",
     "election",
     "mayor",
     "city hall",
     "city manager",
     "county administrator",
     "school board",
     "zoning",
     "permit",
     "vote",
     "voters",
     "millage",
     "tax",
     "public hearing",
     "referendum",
     "annexation",
     "taxes",
     "votes"
    ]
   ],
   "exclude": [
    "football",
    "basketball",
    "baseball",
    "homicide",
    "shooting",
    "arrested",
    "arrest",
    "arrests",
    "charged",
    "sentenced",
    "stabbing",
    "trafficking",
    "crash",
    "killed",
    "fatal",
    "suspect"
   ],
   "feeds": [],
   "color": "#0b5e8f",
   "needs_location": true,
   "skip_listicles": false,
   "icon": "city"
  },
  {
   "id": "local-sports",
   "group": "local",
   "name": "Local Sports ({location})",
   "description": "High school, college and hometown teams near you.",
   "queries": [
    "\"{location}\" (\"high school\" OR prep OR varsity) (football OR basketball OR baseball OR soccer)",
    "\"{location}\" (team OR coach OR championship OR playoff)"
   ],
   "require": [
    [
     "{local_terms}"
    ],
    [
     "high school",
     "prep",
     "varsity",
     "team",
     "coach",
     "football",
     "basketball",
     "baseball",
     "softball",
     "soccer",
     "volleyball",
     "championship",
     "playoff",
     "playoffs",
     "game",
     "wins"
    ]
   ],
   "exclude": [
    "betting odds",
    "sportsbook",
    "arrested",
    "arrest",
    "arrests",
    "charged",
    "sentenced",
    "deputies",
    "shooting",
    "homicide",
    "stabbing",
    "trafficking",
    "crash",
    "killed",
    "fatal",
    "suspect",
    "police",
    "inmate",
    "jail",
    "prison",
    "threat"
   ],
   "feeds": [],
   "color": "#c62828",
   "icon": "trophy",
   "skip_listicles": false,
   "needs_location": true
  },
  {
   "id": "local-events",
   "group": "local",
   "name": "Things to Do ({location})",
   "description": "Festivals, concerts, markets, openings and weekend events near you.",
   "queries": [
    "\"{location}\" (festival OR concert OR fair OR parade OR market)",
    "\"{location}\" (opens OR \"grand opening\" OR weekend OR events OR celebration)"
   ],
   "require": [
    [
     "{local_terms}"
    ],
    [
     "festival",
     "concert",
     "fair",
     "parade",
     "market",
     "opens",
     "opening",
     "grand opening",
     "weekend",
     "event",
     "events",
     "celebration",
     "show",
     "museum",
     "exhibit"
    ]
   ],
   "exclude": [
    "obituary",
    "sponsored content",
    "arrested",
    "arrest",
    "charged",
    "sentenced",
    "homicide"
   ],
   "feeds": [],
   "color": "#008073",
   "icon": "calendar",
   "skip_listicles": true,
   "needs_location": true
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
    "https://www.defenseone.com/rss/all/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://moxie.foxnews.com/google-publisher/politics.xml",
    "https://moxie.foxnews.com/google-publisher/tech.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
   ],
   "color": "#1f3a5f",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "shield"
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
    "https://federalnewsnetwork.com/feed/",
    "https://www.fedweek.com/feed/",
    "https://www.govexec.com/rss/workforce/",
    "https://federalnewsnetwork.com/category/workforce/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://moxie.foxnews.com/google-publisher/politics.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://www.hrdive.com/feeds/news/",
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml"
   ],
   "color": "#0b5e8f",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "people"
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
    "https://federalnewsnetwork.com/feed/",
    "https://www.fedsmith.com/feed/",
    "https://www.fedweek.com/feed/",
    "https://www.govexec.com/rss/pay-benefits/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://www.hrdive.com/feeds/news/"
   ],
   "color": "#1b6e3d",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "coin"
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
   "needs_location": false,
   "icon": "hourglass"
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
    "https://www.nextgov.com/rss/all/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://www.ciodive.com/feeds/news/",
    "https://www.cybersecuritydive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://www.smartcitiesdive.com/feeds/news/"
   ],
   "color": "#34495e",
   "skip_listicles": false,
   "needs_location": false,
   "icon": "capitol"
  },
  {
   "id": "military-veterans",
   "group": "gov",
   "name": "Military and Veterans",
   "description": "Service members, veterans benefits and the VA, deployments and defense budgets.",
   "queries": [
    "(veterans OR \"VA benefits\" OR \"Department of Veterans Affairs\") (benefits OR claims OR care OR rule)",
    "(Army OR Navy OR \"Air Force\" OR Marines OR \"Space Force\") (troops OR deployment OR budget OR \"service members\")"
   ],
   "require": [
    [
     "veterans",
     "veteran",
     "VA",
     "Veterans Affairs",
     "military",
     "troops",
     "service members",
     "Army",
     "Navy",
     "Air Force",
     "Marines",
     "Marine Corps",
     "Space Force",
     "Coast Guard",
     "Pentagon",
     "deployment"
    ]
   ],
   "exclude": [
    "sponsored content",
    "Swiss Army knife",
    "army of fans"
   ],
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/politics.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://moxie.foxnews.com/google-publisher/world.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
   ],
   "color": "#4a5c2a",
   "icon": "medal",
   "skip_listicles": false,
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
   "feeds": [
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Jobs.xml",
    "https://www.highereddive.com/feeds/news/"
   ],
   "topic_feeds": [
    "https://www.hrdive.com/feeds/news/"
   ],
   "color": "#1b6e3d",
   "needs_location": false,
   "icon": "briefcase"
  },
  {
   "id": "education",
   "group": "career",
   "name": "Schools and Education",
   "description": "K-12 schools and colleges: tuition, student loans, testing and education policy.",
   "queries": [
    "(schools OR teachers OR students OR \"school district\") (\"test scores\" OR policy OR funding OR enrollment)",
    "(college OR university OR \"student loans\" OR FAFSA OR tuition) (students OR policy OR costs)"
   ],
   "require": [
    [
     "school",
     "schools",
     "teacher",
     "teachers",
     "students",
     "student",
     "school district",
     "college",
     "colleges",
     "university",
     "universities",
     "student loans",
     "FAFSA",
     "tuition",
     "education",
     "classroom",
     "enrollment"
    ]
   ],
   "exclude": [
    "sponsored content",
    "school of thought",
    "old school"
   ],
   "feeds": [
    "https://www.k12dive.com/feeds/news/",
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml"
   ],
   "color": "#3949ab",
   "icon": "graduation",
   "skip_listicles": false,
   "needs_location": false
  }
 ],
 "packs": [
  {
   "id": "starter",
   "name": "A little of everything",
   "description": "Headlines, the economy, sports, science, travel, an inspiring story and your town.",
   "categories": [
    "us-news",
    "world-news",
    "markets-economy",
    "sports-headlines",
    "health-science",
    "travel",
    "inspiring",
    "local-news"
   ]
  },
  {
   "id": "headlines",
   "name": "Headlines and weather",
   "description": "The day's national and world news, politics, business, severe weather and some good news.",
   "categories": [
    "us-news",
    "world-news",
    "politics",
    "business-news",
    "severe-weather",
    "local-weather",
    "good-news"
   ]
  },
  {
   "id": "sports-fan",
   "name": "Sports fan",
   "description": "Headlines from every sport, plus the NFL, college football, the NBA, MLB, the NHL and soccer.",
   "categories": [
    "sports-headlines",
    "nfl",
    "college-football",
    "nba",
    "mlb",
    "nhl",
    "soccer"
   ]
  },
  {
   "id": "entertainment",
   "name": "Entertainment",
   "description": "Movies, television and streaming, music, books, video games and the arts.",
   "categories": [
    "movies",
    "tv-streaming",
    "music",
    "books",
    "gaming",
    "arts-culture"
   ]
  },
  {
   "id": "science-space",
   "name": "Science and space",
   "description": "Space missions, new discoveries, climate, health research and AI tools.",
   "categories": [
    "space",
    "science-discovery",
    "climate-environment",
    "health-science",
    "ai-tools"
   ]
  },
  {
   "id": "home-family",
   "name": "Home and family",
   "description": "Parenting, food, home and garden, pets, money, travel and things to do nearby.",
   "categories": [
    "parenting-family",
    "food-dining",
    "home-garden",
    "pets",
    "personal-finance",
    "travel",
    "local-events"
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
   "id": "around-town",
   "name": "Around town",
   "description": "Your community, local government, weather and safety, things to do and hometown sports.",
   "categories": [
    "local-news",
    "local-government",
    "local-weather",
    "local-events",
    "local-sports",
    "inspiring"
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
