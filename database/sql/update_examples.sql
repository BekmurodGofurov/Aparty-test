-- Example: verify makler after admin check
UPDATE users
SET is_verified = TRUE
WHERE role = 'makler' AND phone = '+998901119900';

-- Example: mark listing as premium
UPDATE listings
SET is_premium = TRUE,
    premium_expires_at = NOW() + INTERVAL '30 day'
WHERE id = '00000000-0000-0000-0000-000000000000';
