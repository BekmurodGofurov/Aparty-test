// O'zbekistondagi viloyatlar va tumanlar
export const REGIONS_DATA = {
  'Tashkent': ['Bektemir', 'Chilanzar', 'Mirabad', 'Sergeli', 'Shayhantahur', 'Yashnabad', 'Uchtepa', 'Yunusabad'],
  'Andijon': ['Andijon shahri', 'Asaka', 'Asaka tumani', 'Baliqchi', 'Baliqchi tumani', 'Izboskan', 'Izboskan tumani', 'Marhamat', 'Marhamat tumani', 'Paxtaobod', 'Paxtaobod tumani', 'Qo\'rg\'ontepa', 'Qo\'rg\'ontepa tumani', 'Shahrixon', 'Shahrixon tumani', 'Xo\'jaobod', 'Xo\'jaobod tumani'],
  'Bukhara': ['Bukhara City', 'Bukhara', 'Gijduvan', 'Jondor', 'Karakul', 'Kogon', 'Peshku', 'Romitan', 'Shafirkan', 'Vabkent'],
  'Fergana': ['Fergana City', 'Fergana', 'Beshariq', 'Bog\'otan', 'Chust', 'Dangara', 'Furqat', 'Jalalabad', 'Quva', 'Rishtan', 'Sumsoqot', 'Tashloq', 'Yozyovon'],
  'Jizzax': ['Jizzax shahri', 'Jizzax', 'Arnasoy', 'Baxmal', 'Do\'stlik', 'Forish', 'G\'allaorol', 'Mirzacho\'l', 'Paxtakor', 'Yangiobod', 'Zafarobod', 'Zomin'],
  'Kashkadarya': ['Karshi City', 'Kaskadarya', 'Beruni', 'Chiroqchi', 'Dehkonobod', 'Glushkovskiy', 'Koson', 'Muborak', 'Nishon', 'Qamashi', 'Shahrisabz', 'Talimarjon'],
  'Khorezm': ['Urganch City', 'Khorezm', 'Bog\'ot', 'Hazorasp', 'Khiva', 'Shumanay', 'Yangibozor', 'Yangiuli'],
  'Navoiy': ['Navoiy shahri', 'Navoiy', 'Karmana', 'Konimex', 'Navbahor', 'Nurota', 'Qiziltepa', 'Tomdi', 'Uchquduq', 'Xatirchi', 'Zarafshon'],
  'Samarkand': ['Samarkand City', 'Samarkand', 'Bulungur', 'Dargom', 'Jambay', 'Kattakurgan', 'Oqdarya', 'Payariq', 'Urgut', 'Vardanziy'],
  'Sirdarya': ['Guliston City', 'Sirdarya', 'Boyovut', 'Oqqo\'rg\'on', 'Sho\'rchi', 'Shiridarya', 'Xonsa', 'Yangiyer'],
  'Surkhandarya': ['Termiz City', 'Surkhandarya', 'Angor', 'Bandixon', 'Boysun', 'Denov', 'Jarquloq', 'Joliborlar', 'Oltinsoy', 'Parkent', 'Qomoniyot', 'Qonimekh', 'Saryosiya', 'Sherobod'],
  'Tashkent Region': ['Tashkent Region', 'Angren', 'Bekobod', 'Chirchiq', 'Chinobod', 'Gazalkent', 'Kibray', 'Nurafshon', 'Olmaliq', 'Parkent', 'Tashkent', 'Yangiyer', 'Yuqorichirchiq'],
  'Namangan': ['Namangan City', 'Namangan', 'Charbag', 'Chust', 'Kosonsoy', 'Mingbulak', 'Mingkusor', 'Namangan', 'Norman', 'Norin', 'Pap', 'Rishtan', 'Turakurgan', 'Uchkurgan', 'Yangikurgan'],
}

export const getAllRegions = () => Object.keys(REGIONS_DATA)

export const getDistrictsByRegion = (region) => REGIONS_DATA[region] || []

// Room type options
export const ROOM_TYPES = [
  { value: '0', label: 'Barcha turlari' },
  { value: '1', label: 'To\'la kvartira' },
  { value: '2', label: 'Bir xonali kvartira' },
  { value: '3', label: 'Ikkita xonali kvartira' },
  { value: '4', label: 'To\'rt+ xonali kvartira' },
]

// Bosh joy (shared room) options
export const SHARED_ROOM_OPTIONS = [
  { value: '0', label: 'Barcha turlari' },
  { value: '1', label: 'Bosh joy yo\'q' },
  { value: '2', label: 'Bir kishi uchun bosh joy' },
  { value: '3', label: 'Ikki kishiga bosh joy' },
  { value: '4', label: 'Uchta+ kishiga bosh joy' },
]
