"""
Unit tests for password_security module
Tests bcrypt hashing, verification, async operations, and security properties
"""
import unittest
import time
from password_security import (
    hash_password,
    verify_password,
    hash_password_async,
    verify_password_async,
    get_hash_info,
    needs_rehash,
    BCRYPT_ROUNDS
)


class TestPasswordHashing(unittest.TestCase):
    
    def test_basic_hash_and_verify(self):
        """Test basic password hashing and verification"""
        password = "my_secure_password_123"
        hashed = hash_password(password)
        
        # Verify hash format
        self.assertTrue(hashed.startswith('$2b$'))
        self.assertGreater(len(hashed), 50)
        
        # Verify correct password
        self.assertTrue(verify_password(password, hashed))
        
        # Verify wrong password fails
        self.assertFalse(verify_password("wrong_password", hashed))
    
    def test_empty_password_raises_error(self):
        """Test that empty passwords raise ValueError"""
        with self.assertRaises(ValueError):
            hash_password("")
        
        with self.assertRaises(ValueError):
            hash_password(None)
    
    def test_unique_salts(self):
        """Test that same password produces different hashes (unique salts)"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to unique salts
        self.assertNotEqual(hash1, hash2)
        
        # But both should verify correctly
        self.assertTrue(verify_password(password, hash1))
        self.assertTrue(verify_password(password, hash2))
    
    def test_different_rounds(self):
        """Test hashing with different round counts"""
        password = "test_password"
        
        # Hash with different rounds
        hash_10 = hash_password(password, rounds=10)
        hash_12 = hash_password(password, rounds=12)
        hash_14 = hash_password(password, rounds=14)
        
        # All should verify correctly
        self.assertTrue(verify_password(password, hash_10))
        self.assertTrue(verify_password(password, hash_12))
        self.assertTrue(verify_password(password, hash_14))
        
        # Verify round count in hash
        info_10 = get_hash_info(hash_10)
        info_12 = get_hash_info(hash_12)
        info_14 = get_hash_info(hash_14)
        
        self.assertEqual(info_10['rounds'], 10)
        self.assertEqual(info_12['rounds'], 12)
        self.assertEqual(info_14['rounds'], 14)
    
    def test_special_characters(self):
        """Test passwords with special characters"""
        passwords = [
            "p@ssw0rd!",
            "unicode_密码_🔐",
            "spaces in password",
            "tabs\tand\nnewlines",
            "quotes'and\"double",
            "very_long_" + "x" * 100
        ]
        
        for password in passwords:
            hashed = hash_password(password)
            self.assertTrue(verify_password(password, hashed))
            # Use a clearly different wrong password
            self.assertFalse(verify_password("WRONG_PASSWORD_123", hashed))
    
    def test_verify_invalid_hash(self):
        """Test verification with invalid hash formats"""
        password = "test"
        
        # Invalid hash formats should return False, not raise errors
        self.assertFalse(verify_password(password, ""))
        self.assertFalse(verify_password(password, "invalid_hash"))
        self.assertFalse(verify_password(password, "$2b$invalid"))
        self.assertFalse(verify_password("", "some_hash"))
    
    def test_async_hashing(self):
        """Test asynchronous password hashing"""
        password = "async_test_password"
        
        # Hash asynchronously
        future = hash_password_async(password)
        hashed = future.result()
        
        # Verify it works
        self.assertTrue(verify_password(password, hashed))
    
    def test_async_verification(self):
        """Test asynchronous password verification"""
        password = "async_verify_test"
        hashed = hash_password(password)
        
        # Verify asynchronously
        future_correct = verify_password_async(password, hashed)
        future_wrong = verify_password_async("wrong", hashed)
        
        self.assertTrue(future_correct.result())
        self.assertFalse(future_wrong.result())
    
    def test_hash_info_extraction(self):
        """Test extracting information from hash"""
        password = "info_test"
        hashed = hash_password(password, rounds=12)
        
        info = get_hash_info(hashed)
        
        self.assertEqual(info['algorithm'], '2b')
        self.assertEqual(info['rounds'], 12)
        self.assertIn('salt', info)
        self.assertIn('hash', info)
        self.assertEqual(len(info['salt']), 22)  # bcrypt salt is 22 chars
    
    def test_needs_rehash(self):
        """Test rehash detection for security upgrades"""
        password = "rehash_test"
        
        # Hash with low rounds
        old_hash = hash_password(password, rounds=10)
        
        # Should need rehash to higher rounds
        self.assertTrue(needs_rehash(old_hash, target_rounds=12))
        self.assertTrue(needs_rehash(old_hash, target_rounds=14))
        
        # Should not need rehash to same or lower rounds
        self.assertFalse(needs_rehash(old_hash, target_rounds=10))
        self.assertFalse(needs_rehash(old_hash, target_rounds=8))
        
        # Current round hash should not need rehash
        current_hash = hash_password(password, rounds=12)
        self.assertFalse(needs_rehash(current_hash, target_rounds=12))
    
    def test_timing_resistance(self):
        """Test that verification time is consistent (timing attack resistance)"""
        password = "timing_test"
        hashed = hash_password(password)
        
        # Measure time for correct password
        start = time.time()
        verify_password(password, hashed)
        time_correct = time.time() - start
        
        # Measure time for wrong password
        start = time.time()
        verify_password("wrong_password", hashed)
        time_wrong = time.time() - start
        
        # Times should be similar (within 50% of each other)
        # bcrypt is designed to have constant-time comparison
        ratio = max(time_correct, time_wrong) / min(time_correct, time_wrong)
        self.assertLess(ratio, 1.5, "Timing difference too large - potential timing attack vector")
    
    def test_performance_rounds(self):
        """Test that higher rounds take longer (security vs performance trade-off)"""
        password = "performance_test"
        
        # Measure time for different rounds
        start = time.time()
        hash_password(password, rounds=10)
        time_10 = time.time() - start
        
        start = time.time()
        hash_password(password, rounds=12)
        time_12 = time.time() - start
        
        # 12 rounds should take roughly 4x longer than 10 rounds (2^2 = 4)
        # Allow for some variance in measurement
        self.assertGreater(time_12, time_10, "Higher rounds should take longer")
        
        print(f"\nPerformance: 10 rounds={time_10:.3f}s, 12 rounds={time_12:.3f}s")
    
    def test_concurrent_hashing(self):
        """Test multiple concurrent hash operations"""
        passwords = [f"password_{i}" for i in range(10)]
        
        # Hash all passwords concurrently
        futures = [hash_password_async(pwd) for pwd in passwords]
        hashes = [f.result() for f in futures]
        
        # Verify all hashes
        for password, hashed in zip(passwords, hashes):
            self.assertTrue(verify_password(password, hashed))
    
    def test_default_rounds_config(self):
        """Test that default rounds match configuration"""
        password = "config_test"
        hashed = hash_password(password)  # Uses default BCRYPT_ROUNDS
        
        info = get_hash_info(hashed)
        self.assertEqual(info['rounds'], BCRYPT_ROUNDS)


class TestSecurityProperties(unittest.TestCase):
    
    def test_salt_uniqueness(self):
        """Test that salts are cryptographically unique"""
        password = "same_password"
        hashes = [hash_password(password) for _ in range(100)]
        
        # All hashes should be unique
        self.assertEqual(len(hashes), len(set(hashes)))
    
    def test_hash_length_consistency(self):
        """Test that hash length is consistent"""
        passwords = ["short", "medium_length_password", "very_long_" + "x" * 100]
        hashes = [hash_password(pwd) for pwd in passwords]
        
        # All bcrypt hashes should be 60 characters
        for hashed in hashes:
            self.assertEqual(len(hashed), 60)
    
    def test_case_sensitivity(self):
        """Test that passwords are case-sensitive"""
        password = "CaseSensitive"
        hashed = hash_password(password)
        
        self.assertTrue(verify_password("CaseSensitive", hashed))
        self.assertFalse(verify_password("casesensitive", hashed))
        self.assertFalse(verify_password("CASESENSITIVE", hashed))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
