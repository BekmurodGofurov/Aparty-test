import { DEFAULT_ANDIJAN_LOCATION, getDistanceKm } from '../utils/geo'
import { api } from './api'

const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=900&q=80'

const mockProperties = [
  {
    id: 'map-apt-1',
    title: 'Markazdagi yorug 2 xonali kvartira',
    price: 450,
    currency: '$',
    rooms: 2,
    area: 58,
    floor: 6,
    rating: 4.9,
    views: 1240,
    phone: '+998901234567',
    badges: ['Premium', 'Top Pick', 'Verified'],
    description: 'Shahar markazida, liftli yangi uyda joylashgan, mebel va texnikasi bor yorug kvartira.',
    lat: 40.7838,
    lng: 72.3469,
    address: 'Bobur shoh kochasi, Andijon markazi',
    image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1560448075-bb485b067938?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1560440021-33f9b867899d?auto=format&fit=crop&w=1200&q=86',
    ],
  },
  {
    id: 'map-apt-2',
    title: 'Universitet yaqinida talabalar uchun uy',
    price: 280,
    currency: '$',
    rooms: 3,
    area: 72,
    floor: 3,
    rating: 4.7,
    views: 860,
    phone: '+998931112233',
    badges: ['Verified'],
    description: 'Universitetga piyoda borish mumkin, talabalar uchun qulay reja va keng oshxona.',
    lat: 40.7892,
    lng: 72.3398,
    address: 'Universitet kochasi, Andijon',
    image: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=86',
    ],
  },
  {
    id: 'map-apt-3',
    title: 'Premium yangi qurilgan xonadon',
    price: 700,
    currency: '$',
    rooms: 3,
    area: 86,
    floor: 9,
    rating: 5.0,
    views: 2190,
    phone: '+998977778899',
    badges: ['Premium', 'Top Pick', 'Verified'],
    description: 'Premium remont, panorama oynalar, yopiq parking va xavfsiz kirish tizimi mavjud.',
    lat: 40.7757,
    lng: 72.3524,
    address: 'Yangi bozor massivi, Andijon',
    image: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1615873968403-89e068629265?auto=format&fit=crop&w=1200&q=86',
    ],
  },
  {
    id: 'map-apt-4',
    title: 'Oilaviy yashash uchun sokin hovli',
    price: 520,
    currency: '$',
    rooms: 4,
    area: 118,
    floor: 1,
    rating: 4.8,
    views: 1475,
    phone: '+998993334455',
    badges: ['Top Pick', 'Verified'],
    description: 'Oilalar uchun sokin mahalla, hovli, alohida kirish va keng yashash xonasi.',
    lat: 40.7689,
    lng: 72.3316,
    address: 'Mustaqillik mahallasi, Andijon',
    image: 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=86',
    ],
  },
  {
    id: 'map-apt-5',
    title: 'Ixcham studio, transportga yaqin',
    price: 340,
    currency: '$',
    rooms: 1,
    area: 39,
    floor: 5,
    rating: 4.6,
    views: 540,
    phone: '+998944445566',
    badges: ['Verified'],
    description: "Ixcham studio, yakka yashovchilar uchun ideal, transport va do'konlarga yaqin.",
    lat: 40.7948,
    lng: 72.3562,
    address: 'Temir yol vokzali atrofida, Andijon',
    image: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1536376072261-38c75010e6c9?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=86',
    ],
  },
  {
    id: 'map-apt-6',
    title: 'Remontdan chiqqan 2 xona',
    price: 390,
    currency: '$',
    rooms: 2,
    area: 54,
    floor: 4,
    rating: 4.8,
    views: 980,
    phone: '+998955556677',
    badges: ['Premium', 'Verified'],
    description: "Yangi remont, tinch qo'shnilar, konditsioner va zamonaviy oshxona jihozlari bor.",
    lat: 40.7717,
    lng: 72.3614,
    address: 'Navoiy shoh kochasi, Andijon',
    image: 'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=900&q=80',
    images: [
      'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1560185008-b033106af5c3?auto=format&fit=crop&w=1200&q=86',
      'https://images.unsplash.com/photo-1560448204-603b3fc33ddc?auto=format&fit=crop&w=1200&q=86',
    ],
  },
]

const demoDistricts = [
  { name: 'Andijon markazi', baseLat: 40.7821, baseLng: 72.3442 },
  { name: 'Asaka', baseLat: 40.6415, baseLng: 72.2387 },
  { name: 'Shahrixon', baseLat: 40.7135, baseLng: 72.0618 },
  { name: 'Paxtaobod', baseLat: 40.9296, baseLng: 72.4969 },
  { name: "Xo'jaobod", baseLat: 40.6689, baseLng: 72.5601 },
  { name: "Qo'rg'ontepa", baseLat: 40.7317, baseLng: 72.7613 },
  { name: 'Baliqchi', baseLat: 40.9042, baseLng: 71.8471 },
  { name: 'Marhamat', baseLat: 40.4805, baseLng: 72.3138 },
]

const demoImageSets = [
  [
    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=86',
    'https://images.unsplash.com/photo-1560448075-bb485b067938?auto=format&fit=crop&w=1200&q=86',
  ],
  [
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=86',
    'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=86',
  ],
  [
    'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=86',
    'https://images.unsplash.com/photo-1560185008-b033106af5c3?auto=format&fit=crop&w=1200&q=86',
  ],
  [
    'https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1200&q=86',
    'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=86',
  ],
]

const generatedMapProperties = Array.from({ length: 96 }, (_, index) => {
  const district = demoDistricts[index % demoDistricts.length]
  const imageSet = demoImageSets[index % demoImageSets.length]
  const ring = Math.floor(index / demoDistricts.length)
  const angle = ((index * 47) % 360) * (Math.PI / 180)
  const radius = 0.006 + (ring % 6) * 0.004
  const rooms = (index % 4) + 1
  const premium = index % 5 === 0
  const verified = index % 3 !== 0

  return {
    id: `map-demo-${index + 1}`,
    title: `${district.name}dagi ${rooms} xonali demo kvartira`,
    price: 180 + rooms * 85 + (premium ? 90 : 0) + (index % 7) * 12,
    currency: '$',
    rooms,
    area: 28 + rooms * 18 + (index % 11),
    floor: (index % 9) + 1,
    rating: 4.4 + ((index % 6) * 0.1),
    views: 120 + index * 17,
    phone: `+99890${String(5500000 + index).padStart(7, '0')}`,
    badges: [premium ? 'Premium' : null, verified ? 'Verified' : null, index % 7 === 0 ? 'Top Pick' : null].filter(Boolean),
    description: `${district.name} hududida joylashgan demo uy. Mapda ko'proq marker va qidiruv tajribasini sinash uchun qo'shildi.`,
    lat: Number((district.baseLat + Math.sin(angle) * radius).toFixed(6)),
    lng: Number((district.baseLng + Math.cos(angle) * radius).toFixed(6)),
    address: `${district.name}, demo ko'cha ${index + 1}`,
    image: imageSet[0],
    images: imageSet,
  }
})

const allMockProperties = [...mockProperties, ...generatedMapProperties]

const toBadgeList = (listing) => {
  const badges = []
  if (listing.premium) badges.push('Premium')
  if (listing.egasi_verified) badges.push('Verified')
  if ((listing.sharh_soni || 0) > 0) badges.push('Top rated')
  return badges.length ? badges : ['Active']
}

const normalizeListing = (listing, userLocation) => {
  const lat = Number(listing.latitude)
  const lng = Number(listing.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

  const images = Array.isArray(listing.rasmlar) && listing.rasmlar.length
    ? listing.rasmlar
    : [FALLBACK_IMAGE]
  const address = [listing.manzil, listing.tuman, listing.viloyat].filter(Boolean).join(', ')

  return {
    id: listing.id,
    title: listing.manzil || `${listing.tuman || 'Andijon'}dagi ${listing.xonalar_soni || 1} xonali uy`,
    price: Number(listing.narx_usd || 0),
    currency: '$',
    rooms: Number(listing.xonalar_soni || 1),
    area: Number(listing.maydon_m2 || 0) || Math.max(28, Number(listing.xonalar_soni || 1) * 22),
    floor: listing.qavat ?? 1,
    rating: listing.reyting || 4.8,
    views: Number(listing.korishlar || 0),
    phone: listing.egasi_telefon || '',
    badges: toBadgeList(listing),
    description: listing.tavsif || "Qulay joylashuv, tekshirilgan e'lon va tezkor aloqa imkoniyati.",
    lat,
    lng,
    address,
    image: images[0],
    images,
    distanceKm: getDistanceKm(userLocation, { lat, lng }),
  }
}

export async function fetchMapProperties({ userLocation = DEFAULT_ANDIJAN_LOCATION, filters } = {}) {
  try {
    const { data } = await api.get('/listings/search', {
      params: {
        page: 1,
        limit: 300,
        ...(filters || {}),
      },
    })

    const listings = Array.isArray(data?.listings) ? data.listings : []
    const mapped = listings
      .map(listing => normalizeListing(listing, userLocation))
      .filter(Boolean)

    if (mapped.length) {
      return mapped.sort((a, b) => Number(b.badges.includes('Premium')) - Number(a.badges.includes('Premium')) || a.distanceKm - b.distanceKm)
    }
  } catch (error) {
    console.warn('Map listings fallback is active:', error)
  }

  await new Promise(resolve => setTimeout(resolve, 180))

  return allMockProperties
    .map(property => ({
      ...property,
      distanceKm: getDistanceKm(userLocation, { lat: property.lat, lng: property.lng }),
    }))
    .filter(property => {
      const minPrice = Number(filters?.minPrice || 0)
      const maxPrice = Number(filters?.maxPrice || 999999)
      const rooms = filters?.rooms === 'any' ? null : Number(filters?.rooms || 0)

      return property.price >= minPrice &&
        property.price <= maxPrice &&
        (!rooms || property.rooms === rooms)
    })
}

export const mapPropertyApi = {
  fetchNearby: fetchMapProperties,
}
