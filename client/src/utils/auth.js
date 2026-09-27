const HOME_PATHS = {
  owner: '/owner',
  makler: '/makler',
  student: '/profile',
}

export const CHOOSE_ROLE_PATH = '/choose-role'

// Where a signed-in user lands. Users who have not picked a role yet must choose one first.
export const getHomePath = (role) => (role ? HOME_PATHS[role] || '/' : CHOOSE_ROLE_PATH)

export const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) return detail[0]?.msg || fallback
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object') return detail.message || fallback
  return fallback
}
