// Amenity keys shared with the Catalog Service: the create/edit forms save them and search filters on them.
export const AMENITY_KEYS = ['wifi', 'gas', 'water', 'tv', 'air_conditioner', 'washing_machine', 'fridge', 'kitchen']

export const emptyAmenities = () => Object.fromEntries(AMENITY_KEYS.map((key) => [key, false]))
