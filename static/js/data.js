/**
 * AngkorTopUp - Mock Game Data
 * នៅពេលភ្ជាប់ API ពិត ទិន្នន័យនេះនឹងត្រូវបានជំនួសដោយ GET /api/v1/games
 * Base URL: https://khmer-topup.com/api/v1
 */
const GAMES = [
  {
    slug: "mobile-legends",
    name: "Mobile Legends",
    id_label: "User ID",
    server_label: "Zone ID",
    popular: true,
    color: "#1a73e8",
    emoji: "⚔️",
    packages: [
      { package_id: 268, name: "55 Diamonds", price: 0.78, tag: "Popular" },
      { package_id: 269, name: "165 Diamonds", price: 2.28, tag: null },
      { package_id: 270, name: "275 Diamonds", price: 3.78, tag: null },
      { package_id: 271, name: "565 Diamonds", price: 7.58, tag: "Best Value" },
      { package_id: 272, name: "1155 Diamonds", price: 15.18, tag: null },
      { package_id: 273, name: "Weekly Diamond Pass", price: 1.65, tag: "Hot" },
      { package_id: 274, name: "Twilight Pass", price: 8.90, tag: null },
      { package_id: 275, name: "Starlight Membership", price: 4.50, tag: null },
    ]
  },
  {
    slug: "free-fire",
    name: "Free Fire",
    id_label: "Player ID",
    server_label: null,
    popular: true,
    color: "#ff6b00",
    emoji: "🔥",
    packages: [
      { package_id: 301, name: "25 Diamonds", price: 0.24, tag: null },
      { package_id: 302, name: "100 Diamonds", price: 0.90, tag: "Popular" },
      { package_id: 303, name: "310 Diamonds", price: 2.70, tag: null },
      { package_id: 304, name: "520 Diamonds", price: 4.40, tag: null },
      { package_id: 305, name: "1060 Diamonds", price: 8.80, tag: "Best Value" },
      { package_id: 306, name: "Weekly Membership", price: 1.57, tag: "Hot" },
      { package_id: 307, name: "Monthly Membership", price: 7.76, tag: null },
      { package_id: 308, name: "Level Up Package Lv.20", price: 0.61, tag: null },
    ]
  },
  {
    slug: "pubg-mobile",
    name: "PUBG Mobile",
    id_label: "Player ID",
    server_label: null,
    popular: true,
    color: "#f4a261",
    emoji: "🎮",
    packages: [
      { package_id: 401, name: "60 UC", price: 0.95, tag: null },
      { package_id: 402, name: "325 UC", price: 4.80, tag: "Popular" },
      { package_id: 403, name: "660 UC", price: 9.50, tag: null },
      { package_id: 404, name: "1800 UC", price: 24.90, tag: "Best Value" },
      { package_id: 405, name: "3850 UC", price: 49.90, tag: null },
      { package_id: 406, name: "Royalty Pass", price: 3.90, tag: "Hot" },
    ]
  },
  {
    slug: "honor-of-kings",
    name: "Honor of Kings",
    id_label: "User ID",
    server_label: "Server",
    popular: true,
    color: "#c9a227",
    emoji: "👑",
    packages: [
      { package_id: 501, name: "60 Tokens", price: 0.99, tag: null },
      { package_id: 502, name: "300 Tokens", price: 4.79, tag: "Popular" },
      { package_id: 503, name: "980 Tokens", price: 14.90, tag: null },
      { package_id: 504, name: "1980 Tokens", price: 29.90, tag: "Best Value" },
      { package_id: 505, name: "Weekly Card", price: 1.99, tag: "Hot" },
    ]
  },
  {
    slug: "blood-strike",
    name: "Blood Strike",
    id_label: "Player ID",
    server_label: null,
    popular: false,
    color: "#e63946",
    emoji: "🩸",
    packages: [
      { package_id: 601, name: "105 Gold", price: 0.77, tag: "Popular" },
      { package_id: 602, name: "320 Gold", price: 2.29, tag: null },
      { package_id: 603, name: "540 Gold", price: 3.79, tag: null },
      { package_id: 604, name: "1100 Gold", price: 7.49, tag: "Best Value" },
    ]
  },
  {
    slug: "genshin-impact",
    name: "Genshin Impact",
    id_label: "UID",
    server_label: "Server",
    popular: false,
    color: "#48cae4",
    emoji: "🌟",
    packages: [
      { package_id: 701, name: "60 Genesis Crystals", price: 0.99, tag: null },
      { package_id: 702, name: "300+30 Genesis Crystals", price: 4.99, tag: "Popular" },
      { package_id: 703, name: "980+110 Genesis Crystals", price: 14.99, tag: null },
      { package_id: 704, name: "1980+260 Genesis Crystals", price: 29.99, tag: "Best Value" },
      { package_id: 705, name: "Blessing of the Welkin Moon", price: 4.99, tag: "Hot" },
    ]
  },
  {
    slug: "roblox",
    name: "Roblox",
    id_label: "Username",
    server_label: null,
    popular: false,
    color: "#e60012",
    emoji: "🧱",
    packages: [
      { package_id: 801, name: "80 Robux", price: 0.99, tag: null },
      { package_id: 802, name: "400 Robux", price: 4.99, tag: "Popular" },
      { package_id: 803, name: "800 Robux", price: 9.99, tag: null },
      { package_id: 804, name: "1700 Robux", price: 19.99, tag: "Best Value" },
    ]
  },
  {
    slug: "telegram-premium",
    name: "Telegram Premium",
    id_label: "Username / Phone",
    server_label: null,
    popular: true,
    color: "#0088cc",
    emoji: "✈️",
    packages: [
      { package_id: 901, name: "1 Month", price: 4.99, tag: "Popular" },
      { package_id: 902, name: "3 Months", price: 13.99, tag: null },
      { package_id: 903, name: "6 Months", price: 24.99, tag: "Best Value" },
      { package_id: 904, name: "12 Months", price: 44.99, tag: null },
    ]
  },
];

const TICKER_MESSAGES = [
  { user: "18450****", game: "Free Fire", pkg: "WeeklyLite", price: "$0.32" },
  { user: "17850****", game: "Free Fire", pkg: "Monthly", price: "$7.76" },
  { user: "13028****", game: "Free Fire", pkg: "25 Diamonds", price: "$0.24" },
  { user: "9721****", game: "Free Fire", pkg: "100 Diamonds", price: "$0.90" },
  { user: "4029****", game: "Mobile Legends", pkg: "Diamond Pass", price: "$0.81" },
  { user: "15918****", game: "Free Fire", pkg: "100 Diamonds", price: "$0.90" },
  { user: "9609****", game: "Free Fire", pkg: "Weekly", price: "$1.57" },
  { user: "58602****", game: "Blood Strike", pkg: "105 Gold", price: "$0.77" },
  { user: "7408****", game: "Mobile Legends", pkg: "55 Diamonds", price: "$0.76" },
  { user: "2089****", game: "Mobile Legends", pkg: "55 Diamonds", price: "$0.76" },
];
