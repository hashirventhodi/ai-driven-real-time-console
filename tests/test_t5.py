from transformers import T5Tokenizer
import sys

def test_t5_tokenizer():
    """
    Test if t5-small tokenizer is working properly by performing basic tokenization
    and detokenization operations.
    """
    print("Starting T5 tokenizer test...")
    
    try:
        # Initialize tokenizer
        print("Loading t5-small tokenizer...")
        tokenizer = T5Tokenizer.from_pretrained("t5-small")
        
        # Test text
        test_text = "Table users: columns = [id, username, email]"
        
        # Test encoding
        print("\nTesting encoding...")
        encoded = tokenizer.encode(test_text)
        print(f"Encoded tokens: {encoded[:10]}...")
        print(f"Number of tokens: {len(encoded)}")
        
        # Test decoding
        print("\nTesting decoding...")
        decoded = tokenizer.decode(encoded)
        print(f"Original text: {test_text}")
        print(f"Decoded text: {decoded}")
        
        # Test if encoding/decoding preserves meaning
        if test_text.strip() in decoded:
            print("\n✅ Test passed! T5 tokenizer is working correctly.")
            return True
        else:
            print("\n❌ Test failed! Decoded text doesn't match original.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error occurred during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_t5_tokenizer()
    sys.exit(0 if success else 1)