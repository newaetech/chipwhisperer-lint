try:
    from chipwhisperer.analyzer.attacks.models.aes.funcs import subbytes, mixcolumns, shiftrows, inv_subbytes, inv_mixcolumns, inv_shiftrows
    from chipwhisperer.analyzer.attacks.models.aes.key_schedule import keyScheduleRounds
except ImportError:
    print "Note: can't find ChipWhisperer Analyzer functions for AES"
    print "Importing local copy..."
    from aes_helper import *
    


    
class Leakage_Base(object):
    name = 'Leakage model base class'
    
    # TODO: autogenerate (or automatically validate) these lists
    leakage_points = []
    
    def cipher(self):
        raise NotImplementedError()
    
    
    
class AES128_Leakage(Leakage_Base):
    # Implements AES-128, saving internal states in a dictionary for analysis
    name = 'AES128'
    ks = None
    
    leakage_points = [
        "Plaintext",
        "Key",
        "Round 0: AddRoundKey Output",
        "Round 1: SubBytes Output",
        "Round 1: ShiftRows Output",
        "Round 1: MixColumns Output",
        "Round 1: RoundKey",
        "Round 1: AddRoundKey Output",
        "Round 2: SubBytes Output",
        "Round 2: ShiftRows Output",
        "Round 2: MixColumns Output",
        "Round 2: RoundKey",
        "Round 2: AddRoundKey Output",
        "Round 3: SubBytes Output",
        "Round 3: ShiftRows Output",
        "Round 3: MixColumns Output",
        "Round 3: RoundKey",
        "Round 3: AddRoundKey Output",
        "Round 4: SubBytes Output",
        "Round 4: ShiftRows Output",
        "Round 4: MixColumns Output",
        "Round 4: RoundKey",
        "Round 4: AddRoundKey Output",
        "Round 5: SubBytes Output",
        "Round 5: ShiftRows Output",
        "Round 5: RoundKey",
        "Round 5: MixColumns Output",
        "Round 5: AddRoundKey Output",
        "Round 6: SubBytes Output",
        "Round 6: ShiftRows Output",
        "Round 6: MixColumns Output",
        "Round 6: RoundKey",
        "Round 6: AddRoundKey Output",
        "Round 7: SubBytes Output",
        "Round 7: ShiftRows Output",
        "Round 7: MixColumns Output",
        "Round 7: RoundKey",
        "Round 7: AddRoundKey Output",
        "Round 8: SubBytes Output",
        "Round 8: ShiftRows Output",
        "Round 8: MixColumns Output",
        "Round 8: RoundKey",
        "Round 8: AddRoundKey Output",
        "Round 9: SubBytes Output",
        "Round 9: ShiftRows Output",
        "Round 9: MixColumns Output",
        "Round 9: RoundKey",
        "Round 9: AddRoundKey Output",
        "Round 10: SubBytes Output",
        "Round 10: ShiftRows Output",
        "Round 10: RoundKey",
        "Ciphertext"]
        
    def __init__(self):
        self.ks = None
        
    def flatten(self, state):
        ret = 0
        for i in range(16):
            ret <<= 8
            ret |= state[i]
            ret = ret & ((1 << 128) - 1)
        return ret
        
    def cipher(self, pt, key):
        # Note: we assume fixed key here for huge speedup
        # TODO: make this an option
        #if self.ks is None:
        self.ks = [keyScheduleRounds(key, 0, r) for r in range(11)]
    
        ret = {}
        
        Nr = 10
        state = pt
        ret['Plaintext'] = self.flatten(state[:])
        
        ret['Key'] = self.flatten(self.ks[0])
        
        state = [state[i] ^ self.ks[0][i] for i in range(16)]
        ret['Round 0: AddRoundKey Output'] = self.flatten(state[:])
        
        for r in range(1, Nr):
            state = subbytes(state)
            ret['Round ' + str(r) + ': SubBytes Output'] = self.flatten(state[:])
            
            state = shiftrows(state)
            ret['Round ' + str(r) + ': ShiftRows Output'] = self.flatten(state[:])
            
            state = mixcolumns(state)
            ret['Round ' + str(r) + ': MixColumns Output'] = self.flatten(state[:])
        
            ret['Round ' + str(r) + ': RoundKey'] = self.flatten(self.ks[r])
        
            state = [state[i] ^ self.ks[r][i] for i in range(16)]
            ret['Round ' + str(r) + ': AddRoundKey Output'] = self.flatten(state[:])
        
        
        
        state = subbytes(state)
        ret['Round 10: SubBytes Output'] = self.flatten(state[:])
        
        state = shiftrows(state)
        ret['Round 10: ShiftRows Output'] = self.flatten(state[:])
        
        ret['Round 10: RoundKey'] = self.flatten(self.ks[Nr])
        
        state = [state[i] ^ self.ks[Nr][i] for i in range(16)]
        ret['Ciphertext'] = self.flatten(state[:])
        
        return ret
        
class AES128_SRSBOX_Leakage(Leakage_Base):
    # Implements AES-128, saving internal states in a dictionary for analysis
    name = 'AES128_SHIFTROWSFIRST'
    ks = None
    
    leakage_points = [
        "Plaintext",
        "Key",
        "Round 0: AddRoundKey Output",
        "Round 1: SubBytes Output",
        "Round 1: ShiftRows Output",
        "Round 1: MixColumns Output",
        "Round 1: RoundKey",
        "Round 1: AddRoundKey Output",
        "Round 2: SubBytes Output",
        "Round 2: ShiftRows Output",
        "Round 2: MixColumns Output",
        "Round 2: RoundKey",
        "Round 2: AddRoundKey Output",
        "Round 3: SubBytes Output",
        "Round 3: ShiftRows Output",
        "Round 3: MixColumns Output",
        "Round 3: RoundKey",
        "Round 3: AddRoundKey Output",
        "Round 4: SubBytes Output",
        "Round 4: ShiftRows Output",
        "Round 4: MixColumns Output",
        "Round 4: RoundKey",
        "Round 4: AddRoundKey Output",
        "Round 5: SubBytes Output",
        "Round 5: ShiftRows Output",
        "Round 5: RoundKey",
        "Round 5: MixColumns Output",
        "Round 5: AddRoundKey Output",
        "Round 6: SubBytes Output",
        "Round 6: ShiftRows Output",
        "Round 6: MixColumns Output",
        "Round 6: RoundKey",
        "Round 6: AddRoundKey Output",
        "Round 7: SubBytes Output",
        "Round 7: ShiftRows Output",
        "Round 7: MixColumns Output",
        "Round 7: RoundKey",
        "Round 7: AddRoundKey Output",
        "Round 8: SubBytes Output",
        "Round 8: ShiftRows Output",
        "Round 8: MixColumns Output",
        "Round 8: RoundKey",
        "Round 8: AddRoundKey Output",
        "Round 9: SubBytes Output",
        "Round 9: ShiftRows Output",
        "Round 9: MixColumns Output",
        "Round 9: RoundKey",
        "Round 9: AddRoundKey Output",
        "Round 10: SubBytes Output",
        "Round 10: ShiftRows Output",
        "Round 10: RoundKey",
        "Ciphertext"]
        
    def __init__(self):
        self.ks = None
        
    def flatten(self, state):
        ret = 0
        for i in range(16):
            ret <<= 8
            ret |= state[i]
            ret = ret & ((1 << 128) - 1)
        return ret
        
    def cipher(self, pt, key):
        # Note: we assume fixed key here for huge speedup
        # TODO: make this an option
        #if self.ks is None:
        self.ks = [keyScheduleRounds(key, 0, r) for r in range(11)]
    
        ret = {}
        
        Nr = 10
        state = pt
        ret['Plaintext'] = self.flatten(state[:])
        
        ret['Key'] = self.flatten(self.ks[0])
        
        state = [state[i] ^ self.ks[0][i] for i in range(16)]
        ret['Round 0: AddRoundKey Output'] = self.flatten(state[:])
        
        state = shiftrows(state)
        ret['Round 1: ShiftRows Output'] = self.flatten(state[:])
        
        for r in range(1, Nr+1):
            state = subbytes(state)
            ret['Round ' + str(r) + ': SubBytes Output'] = self.flatten(state[:])
            
            if r == Nr:
                break
                        
            state = mixcolumns(state)
            ret['Round ' + str(r) + ': MixColumns Output'] = self.flatten(state[:])
        
            ret['Round ' + str(r) + ': RoundKey'] = self.flatten(self.ks[r])
        
            state = [state[i] ^ self.ks[r][i] for i in range(16)]
            ret['Round ' + str(r) + ': AddRoundKey Output'] = self.flatten(state[:])
            
            state = shiftrows(state)
            ret['Round ' + str(r+1) + ': ShiftRows Output'] = self.flatten(state[:])
               
        ret['Round 10: RoundKey'] = self.flatten(self.ks[Nr])
        
        state = [state[i] ^ self.ks[Nr][i] for i in range(16)]
        ret['Ciphertext'] = self.flatten(state[:])
        
        return ret
        
class AES256_Leakage(Leakage_Base):
    name = 'AES256'
    leakage_points = [
        "Plaintext",
        "Key (bytes 0-15)",
        "Key (bytes 16-31)",
        "Round 0: AddRoundKey Output",
        "Round 1: SubBytes Output",
        "Round 1: ShiftRows Output",
        "Round 1: MixColumns Output",
        "Round 1: AddRoundKey Output",
        "Round 2: SubBytes Output",
        "Round 2: ShiftRows Output",
        "Round 2: MixColumns Output",
        "Round 2: AddRoundKey Output",
        "Round 3: SubBytes Output",
        "Round 3: ShiftRows Output",
        "Round 3: MixColumns Output",
        "Round 3: AddRoundKey Output",
        "Round 4: SubBytes Output",
        "Round 4: ShiftRows Output",
        "Round 4: MixColumns Output",
        "Round 4: AddRoundKey Output",
        "Round 5: SubBytes Output",
        "Round 5: ShiftRows Output",
        "Round 5: MixColumns Output",
        "Round 5: AddRoundKey Output",
        "Round 6: SubBytes Output",
        "Round 6: ShiftRows Output",
        "Round 6: MixColumns Output",
        "Round 6: AddRoundKey Output",
        "Round 7: SubBytes Output",
        "Round 7: ShiftRows Output",
        "Round 7: MixColumns Output",
        "Round 7: AddRoundKey Output",
        "Round 8: SubBytes Output",
        "Round 8: ShiftRows Output",
        "Round 8: MixColumns Output",
        "Round 8: AddRoundKey Output",
        "Round 9: SubBytes Output",
        "Round 9: ShiftRows Output",
        "Round 9: MixColumns Output",
        "Round 9: AddRoundKey Output",
        "Round 10: SubBytes Output",
        "Round 10: ShiftRows Output",
        "Round 10: MixColumns Output",
        "Round 10: AddRoundKey Output",
        "Round 11: SubBytes Output",
        "Round 11: ShiftRows Output",
        "Round 11: MixColumns Output",
        "Round 11: AddRoundKey Output",
        "Round 12: SubBytes Output",
        "Round 12: ShiftRows Output",
        "Round 12: MixColumns Output",
        "Round 12: AddRoundKey Output",
        "Round 13: SubBytes Output",
        "Round 13: ShiftRows Output",
        "Round 13: MixColumns Output",
        "Round 13: AddRoundKey Output",
        "Round 14: SubBytes Output",
        "Round 14: ShiftRows Output",
        "Ciphertext"]
    
    def __init__(self):
        self.ks = None
        
    def flatten(self, state):
        ret = 0
        for i in range(16):
            ret <<= 8
            ret |= state[i]
        return ret
        
    def cipher(self, pt, key):
        Nr = 14
        if self.ks is None:
            self.ks = [keyScheduleRounds(key, 0, r) for r in range(Nr+1)]
    
        ret = {}
        
        state = pt
        ret['Plaintext'] = self.flatten(state[:])
        
        ret['Key (bytes 0-15)']  = self.flatten(self.ks[0])
        ret['Key (bytes 16-31)'] = self.flatten(self.ks[1])
        
        state = [state[i] ^ self.ks[0][i] for i in range(16)]
        ret['Round 0: AddRoundKey Output'] = self.flatten(state[:])
        
        for r in range(1, Nr):
            state = subbytes(state)
            ret['Round ' + str(r) + ': SubBytes Output'] = self.flatten(state[:])
            
            state = shiftrows(state)
            ret['Round ' + str(r) + ': ShiftRows Output'] = self.flatten(state[:])
            
            state = mixcolumns(state)
            ret['Round ' + str(r) + ': MixColumns Output'] = self.flatten(state[:])
            
            state = [state[i] ^ self.ks[r][i] for i in range(16)]
            ret['Round ' + str(r) + ': AddRoundKey Output'] = self.flatten(state[:])
        
        
        state = subbytes(state)
        ret['Round 14: SubBytes Output'] = self.flatten(state[:])
        
        state = shiftrows(state)
        ret['Round 14: ShiftRows Output'] = self.flatten(state[:])
        
        state = [state[i] ^ self.ks[Nr][i] for i in range(16)]
        ret['Ciphertext'] = self.flatten(state[:])
        
        return ret
        
class AES256_Decryption_Leakage(Leakage_Base):
    name = 'AES256_DEC'
    leakage_points = [
        "Plaintext",
        "Key (bytes 0-15)",
        "Key (bytes 16-31)",
        "Round 0: AddRoundKey Output",
        "Round 1: SubBytes Output",
        "Round 1: ShiftRows Output",
        "Round 1: MixColumns Output",
        "Round 1: AddRoundKey Output",
        "Round 2: SubBytes Output",
        "Round 2: ShiftRows Output",
        "Round 2: MixColumns Output",
        "Round 2: AddRoundKey Output",
        "Round 3: SubBytes Output",
        "Round 3: ShiftRows Output",
        "Round 3: MixColumns Output",
        "Round 3: AddRoundKey Output",
        "Round 4: SubBytes Output",
        "Round 4: ShiftRows Output",
        "Round 4: MixColumns Output",
        "Round 4: AddRoundKey Output",
        "Round 5: SubBytes Output",
        "Round 5: ShiftRows Output",
        "Round 5: MixColumns Output",
        "Round 5: AddRoundKey Output",
        "Round 6: SubBytes Output",
        "Round 6: ShiftRows Output",
        "Round 6: MixColumns Output",
        "Round 6: AddRoundKey Output",
        "Round 7: SubBytes Output",
        "Round 7: ShiftRows Output",
        "Round 7: MixColumns Output",
        "Round 7: AddRoundKey Output",
        "Round 8: SubBytes Output",
        "Round 8: ShiftRows Output",
        "Round 8: MixColumns Output",
        "Round 8: AddRoundKey Output",
        "Round 9: SubBytes Output",
        "Round 9: ShiftRows Output",
        "Round 9: MixColumns Output",
        "Round 9: AddRoundKey Output",
        "Round 10: SubBytes Output",
        "Round 10: ShiftRows Output",
        "Round 10: MixColumns Output",
        "Round 10: AddRoundKey Output",
        "Round 11: SubBytes Output",
        "Round 11: ShiftRows Output",
        "Round 11: MixColumns Output",
        "Round 11: AddRoundKey Output",
        "Round 12: SubBytes Output",
        "Round 12: ShiftRows Output",
        "Round 12: MixColumns Output",
        "Round 12: AddRoundKey Output",
        "Round 13: SubBytes Output",
        "Round 13: ShiftRows Output",
        "Round 13: MixColumns Output",
        "Round 13: AddRoundKey Output",
        "Round 14: SubBytes Output",
        "Round 14: ShiftRows Output",
        "Ciphertext (Unflipped)",
        "Ciphertext (Flipped)"]
    
    def __init__(self):
        self.ks = None
        
    def flatten(self, state):
        ret = 0L
        for i in range(16):
            ret <<= 8
            ret = ret | state[i]
            ret = ret & ((1 << 128) - 1)
        return ret
        
    def reverse_bits(self, x):
        for i in range(len(x))[::4]:
            xi = ((x[i]<<24) | (x[i+1]<<16) | (x[i+2]<<8) | (x[i+3]<<0)) & ((1 << 32) - 1)
            b = "{:032b}".format(xi)[::-1]
            xrev = int(b, 2)
            x[i]   = (xrev >> 24) & 0xFF
            x[i+1] = (xrev >> 16) & 0xFF
            x[i+2] = (xrev >>  8) & 0xFF
            x[i+3] = (xrev >>  0) & 0xFF
        return x
        
    def cipher(self, input, key):
        Nr = 14
        #if self.ks is None:
        self.ks = [keyScheduleRounds(key, 0, r) for r in range(Nr+1)]
    
        ret = {}
        
        state = input
        ret['Ciphertext (Unflipped)'] = self.flatten(state)
        
        
        ret['Key (bytes 0-15)']  = self.flatten(self.ks[0])
        ret['Key (bytes 16-31)'] = self.flatten(self.ks[1])
        
        state = self.reverse_bits(input)
        ret['Ciphertext (Flipped)'] = self.flatten(state)
        state = [state[i] ^ self.ks[Nr][i] for i in range(16)]
        
        ret['Round 14: ShiftRows Output'] = self.flatten(state[:])
        state = inv_shiftrows(state)
        
        ret['Round 14: SubBytes Output'] = self.flatten(state[:])
        state = inv_subbytes(state)
     
        for r in reversed(range(1, Nr)):
            ret['Round ' + str(r) + ': AddRoundKey Output'] = self.flatten(state[:])
            state = [state[i] ^ self.ks[r][i] for i in range(16)]
            
            ret['Round ' + str(r) + ': MixColumns Output'] = self.flatten(state[:])
            state = inv_mixcolumns(state)
            
            ret['Round ' + str(r) + ': ShiftRows Output'] = self.flatten(state[:])
            state = inv_shiftrows(state)
            
            ret['Round ' + str(r) + ': SubBytes Output'] = self.flatten(state[:])
            state = inv_subbytes(state)
        
        ret['Round 0: AddRoundKey Output'] = self.flatten(state[:])
        state = [state[i] ^ self.ks[0][i] for i in range(16)]
        
        
        ret['Plaintext'] = self.flatten(state[:])
        
        return ret
        
class XOR256_Leakage(Leakage_Base):
    name = 'XOR256'
    leakage_points = [
        "Plaintext",
        "Key",
        "Ciphertext"]
    
    def __init__(self):
        pass
        
    def flatten(self, state):
        ret = 0L
        for i in range(32):
            ret <<= 8
            ret = ret | state[i]
            ret = ret & ((1 << 128) - 1)
        return ret
        
    def cipher(self, input, key):
        ret = {}
        ret['Plaintext'] = self.flatten(input)
        ret['Key'] = self.flatten(key)
        
        for i in range(32):
            input[i] ^= key[i]
        ret['Ciphertext'] = self.flatten(input)
        
        return ret
        
class XOR128_Leakage(Leakage_Base):
    name = 'XOR128'
    leakage_points = [
        "Plaintext",
        "Key",
        "Ciphertext"]
    
    def __init__(self):
        pass
        
    def flatten(self, state):
        ret = 0L
        for i in range(16):
            ret <<= 8
            ret = ret | state[i]
            ret = ret & ((1 << 128) - 1)
        return ret
        
    def cipher(self, input, key):
        ret = {}
        ret['Plaintext'] = self.flatten(input)
        ret['Key'] = self.flatten(key)
        
        for i in range(16):
            input[i] ^= key[i]
        ret['Ciphertext'] = self.flatten(input)
        
        return ret
        
models = [
    AES128_Leakage,
    AES128_SRSBOX_Leakage,
    AES256_Leakage,
    AES256_Decryption_Leakage,
    XOR128_Leakage,
    XOR256_Leakage,
    ]