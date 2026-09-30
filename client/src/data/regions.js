// O'zbekistondagi viloyatlar va tumanlar
export const REGIONS_DATA = {
  'Tashkent': ['Olmazor', 'Chilanzar', 'Yunusabad', 'Mirzo Ulugbek', 'Mirabad', 'Yakkasaray', 'Shayhantahur', 'Yashnabad', 'Uchtepa', 'Sergeli', 'Bektemir', 'Yangihayot'],
  'Tashkent Region': ['Nurafshon', 'Angren', 'Bekobod', 'Chirchiq', 'Olmaliq', 'Yangiyo‘l', 'Bo‘stonliq', 'Bo‘ka', 'Zangiota', 'Qibray', 'Parkent', 'Piskent', 'O‘rtachirchiq', 'Chinoz', 'Yuqorichirchiq', 'Yangiyo‘l tumani', 'Toshkent tumani'],
  'Andijon': ['Andijon shahri', 'Asaka', 'Baliqchi', 'Bo‘ston', 'Buloqboshi', 'Izboskan', 'Jalaquduq', 'Marhamat', 'Oltinko‘l', 'Paxtaobod', 'Qo‘rg‘ontepa', 'Shahrixon', 'Ulug‘nor', 'Xo‘jaobod'],
  'Bukhara': ['Buxoro shahri', 'Kogon shahri', 'Buxoro tumani', 'G‘ijduvon', 'Jondor', 'Kogon tumani', 'Olot', 'Peshku', 'Qorako‘l', 'Qorovulbozor', 'Romitan', 'Shofirkon', 'Vobkent'],
  'Fergana': ['Farg‘ona shahri', 'Marg‘ilon shahri', 'Qo‘qon shahri', 'Quvasoy', 'Beshariq', 'Bog‘dod', 'Buvayda', 'Dang‘ara', 'Farg‘ona tumani', 'Furqat', 'Oltiariq', 'Qo‘shtepa', 'Quva', 'Rishton', 'So‘x', 'Toshloq', 'Uchko‘prik', 'Yozyovon'],
  'Jizzax': ['Jizzax shahri', 'Arnasoy', 'Baxmal', 'Do‘stlik', 'Forish', 'G‘allaorol', 'Sharof Rashidov', 'Mirzacho‘l', 'Paxtakor', 'Yangiobod', 'Zomin', 'Zafarobod', 'Zarbdor'],
  'Kashkadarya': ['Qarshi shahri', 'Shahrisabz shahri', 'Chiroqchi', 'Dehqonobod', 'G‘uzor', 'Kasbi', 'Kitob', 'Koson', 'Mirishkor', 'Muborak', 'Nishon', 'Qamashi', 'Qarshi tumani', 'Shahrisabz tumani', 'Yakkabog‘', 'Ko‘kdala'],
  'Khorezm': ['Urganch shahri', 'Xiva shahri', 'Bog‘ot', 'Gurlan', 'Hazorasp', 'Xiva tumani', 'Qo‘shko‘pir', 'Shovot', 'Tuproqqal‘a', 'Urganch tumani', 'Xonqa', 'Yangiariq', 'Yangibozor'],
  'Namangan': ['Namangan shahri', 'Chortoq', 'Chust', 'Kosonsoy', 'Mingbuloq', 'Namangan tumani', 'Norin', 'Pop', 'To‘raqo‘rg‘on', 'Uychi', 'Uchqo‘rg‘on', 'Yangiqo‘rg‘on', 'Davlatobod', 'Yangi Namangan'],
  'Navoiy': ['Navoiy shahri', 'Zarafshon shahri', 'Karmana', 'Konimex', 'Navbahor', 'Nurota', 'Qiziltepa', 'Tomdi', 'Uchquduq', 'Xatirchi'],
  'Samarkand': ['Samarqand shahri', 'Kattaqo‘rg‘on shahri', 'Bulung‘ur', 'Ishtixon', 'Jomboy', 'Kattaqo‘rg‘on tumani', 'Narpay', 'Nurobod', 'Oqdaryo', 'Paxtachi', 'Payariq', 'Pastdarg‘om', 'Samarqand tumani', 'Toyloq', 'Urgut'],
  'Sirdarya': ['Guliston shahri', 'Shirin shahri', 'Yangiyer shahri', 'Boyovut', 'Guliston tumani', 'Mirzaobod', 'Oqoltin', 'Sardoba', 'Sayxunobod', 'Sirdaryo tumani', 'Xovos'],
  'Surkhandarya': ['Termiz shahri', 'Angor', 'Bandixon', 'Boysun', 'Denov', 'Jarqo‘rg‘on', 'Muzrabot', 'Oltinsoy', 'Qiziriq', 'Qumqo‘rg‘on', 'Sariosiyo', 'Sherobod', 'Sho‘rchi', 'Termiz tumani', 'Uzun'],
  'Qoraqalpog‘iston': ['Nukus shahri', 'Amudaryo', 'Beruniy', 'Bo‘zatov', 'Qorao‘zak', 'Kegeyli', 'Qo‘ng‘irot', 'Qonliko‘l', 'Mo‘ynoq', 'Nukus tumani', 'Taxiatosh', 'Taxtako‘pir', 'To‘rtko‘l', 'Xo‘jayli', 'Chimboy', 'Shumanay', 'Ellikqala'],
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
