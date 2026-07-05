import { useEffect, useRef, useState } from 'react'

/**
 * useScrollAnimation Hook
 * Triggers animations when elements scroll into view
 */
export function useScrollAnimation(threshold = 0.2) {
    const ref = useRef(null)
    const [isVisible, setIsVisible] = useState(false)

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true)
                    observer.unobserve(entry.target)
                }
            },
            { threshold }
        )

        if (ref.current) {
            observer.observe(ref.current)
        }

        return () => observer.disconnect()
    }, [threshold])

    return [ref, isVisible]
}

/**
 * useParallax Hook
 * Creates parallax scroll effect
 */
export function useParallax(speed = 0.5) {
    const ref = useRef(null)
    const [offset, setOffset] = useState(0)

    useEffect(() => {
        const handleScroll = () => {
            if (ref.current) {
                const rect = ref.current.getBoundingClientRect()
                const elementCenter = rect.top + rect.height / 2
                const windowCenter = window.innerHeight / 2
                const distance = elementCenter - windowCenter
                setOffset(distance * speed)
            }
        }

        window.addEventListener('scroll', handleScroll, { passive: true })
        return () => window.removeEventListener('scroll', handleScroll)
    }, [speed])

    return [ref, offset]
}
