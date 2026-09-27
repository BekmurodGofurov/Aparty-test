import { createHttpCache } from './httpCache'

export const browserCache = createHttpCache({ storage: window.localStorage })
