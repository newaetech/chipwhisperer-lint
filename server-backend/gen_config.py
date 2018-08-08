import itertools

def aes128_brute_force():
    fname = "config/aes128_brute_force.cfg"
    
    from server.models import AES128_Leakage
    lt = AES128_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write("AES128\n")
        for (lt1, lt2) in itertools.combinations_with_replacement(lt, 2):
            if lt1 == lt2:
                name = "HW: %s" % lt1
            else:
                name = "HD: %s to %s" % (lt1, lt2)
            
            m1 = "FF000000000000000000000000000000"
            
            if lt1 == lt2:
                m2 = "00000000000000000000000000000000"
            else:
                m2 = "FF000000000000000000000000000000"
            op = "N"
            
            f.write(name + '\n')
            f.write(lt1  + '\n')
            f.write(m1   + '\n')
            f.write(lt2  + '\n')
            f.write(m2   + '\n')
            f.write(op   + '\n')
            f.write("\n")
        
def aes128_simple():
    fname = "config/aes128_simple.cfg"
    
    from server.models import AES128_Leakage
    lt = AES128_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write("AES128\n")
        for i in range(len(lt)):
            end = min(len(lt), i+5)
            for j in range(i, end):
                lt1 = lt[i]
                lt2 = lt[j]
                if lt1 == lt2:
                    name = "HW: %s" % lt1
                else:
                    name = "HD: %s to %s" % (lt1, lt2)
                
                m1 = "FF000000000000000000000000000000"
                
                if lt1 == lt2:
                    m2 = "00000000000000000000000000000000"
                else:
                    m2 = "FF000000000000000000000000000000"
                op = "N"
                
                f.write(name + '\n')
                f.write(lt1  + '\n')
                f.write(m1   + '\n')
                f.write(lt2  + '\n')
                f.write(m2   + '\n')
                f.write(op   + '\n')
                f.write("\n")
                
def aes128_sbox():
    fname = "config/aes128_sbox.cfg"
    
    from server.models import AES128_Leakage
    lt = AES128_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write("AES128\n")
        for i in range(len(lt)):
            if "SubBytes" not in lt[i]:
                continue
                
            lt1 = lt2 = lt[i]
            m1 = 0xFF000000000000000000000000000000
            m2 = 0x00000000000000000000000000000000
            for j in range(16):
                if j == 0:
                    name = "HW: %s byte 0" % lt1
                    op = "N"
                else:
                    name = "HD: %s byte %d to byte %d" % (lt1, j-1, j)
                    op = "R 8"
                m1_str = "{:032x}".format(m1)
                m2_str = "{:032x}".format(m2)
                f.write(name   + '\n')
                f.write(lt1    + '\n')
                f.write(m1_str + '\n')
                f.write(lt2    + '\n')
                f.write(m2_str + '\n')
                f.write(op     + '\n')
                f.write("\n")
                
                m2 = m1
                m1 = m1 >> 8
                
def aes128_sbox_dpa():
    fname = "config/aes128_sbox_dpa.cfg"
    
    from server.models import AES128_Leakage
    lt = AES128_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write("AES128\n")
        for i in range(len(lt)):
            if "SubBytes" not in lt[i]:
                continue
                
            lt1 = lt2 = lt[i]
            m1 = 0x01000000000000000000000000000000
            m2 = 0x00000000000000000000000000000000
            for j in range(1):
                if j == 0:
                    name = "HW: %s byte 0 (bit 0)" % lt1
                    op = "N"
                else:
                    name = "HD: %s byte %d to byte %d (bit 0)" % (lt1, j-1, j)
                    op = "R 8"
                m1_str = "{:032x}".format(m1)
                m2_str = "{:032x}".format(m2)
                f.write(name   + '\n')
                f.write(lt1    + '\n')
                f.write(m1_str + '\n')
                f.write(lt2    + '\n')
                f.write(m2_str + '\n')
                f.write(op     + '\n')
                f.write("\n")
                
                m2 = m1
                m1 = m1 >> 8
                
def aes128_sbox_value():
    fname = "config/aes128_sbox_value.cfg"
    
    from server.models import AES128_Leakage
    lt = AES128_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write("AES128\n")
        
        lt1 = lt2 = "Round 1: SubBytes Output"
        m1 = 0xFF000000000000000000000000000000
        m2 = 0x00000000000000000000000000000000
        m1_str = "{:032x}".format(m1)
        m2_str = "{:032x}".format(m2)
        
        for i in range(16):
            name = "Value: Round 1 SubBytes byte 0 = %d" % i
            val = i << (128 - 8)
            op = "E 0x%032x" % val
            
            f.write(name   + '\n')
            f.write(lt1    + '\n')
            f.write(m1_str + '\n')
            f.write(lt2    + '\n')
            f.write(m2_str + '\n')
            f.write(op     + '\n')
            f.write("\n")
                
def aes256_dec_simple():
    fname = "config/aes256dec_simple.cfg"
    
    from server.models import AES256_Decryption_Leakage
    lt = AES256_Decryption_Leakage.leakage_points
    
    with open(fname, "w") as f:
        f.write(AES256_Decryption_Leakage.name + "\n")
        for i in range(len(lt)):
            end = min(len(lt), i+5)
            for j in range(i, end):
                lt1 = lt[i]
                lt2 = lt[j]
                if lt1 == lt2:
                    name = "HW: %s" % lt1
                else:
                    name = "HD: %s to %s" % (lt1, lt2)
                
                m1 = "FF000000000000000000000000000000"
                
                if lt1 == lt2:
                    m2 = "00000000000000000000000000000000"
                else:
                    m2 = "FF000000000000000000000000000000"
                op = "N"
                
                f.write(name + '\n')
                f.write(lt1  + '\n')
                f.write(m1   + '\n')
                f.write(lt2  + '\n')
                f.write(m2   + '\n')
                f.write(op   + '\n')
                f.write("\n")
                
def aes256_bitstream():
    fname = "config/aes256dec_bitstream.cfg"
    
    from server.models import AES256_Decryption_Leakage
    lt = AES256_Decryption_Leakage.leakage_points
    ltr = [s for s in lt if 'SubBytes' in s]
    
    with open(fname, "w") as f:
        f.write(AES256_Decryption_Leakage.name + "\n")
        for (lt1, lt2) in itertools.combinations_with_replacement(ltr, 2):
            if lt1 == lt2:
                name = "HW: %s" % lt1
            else:
                name = "HD: %s to %s" % (lt1, lt2)
            
            m1 = "FF000000000000000000000000000000"
            
            if lt1 == lt2:
                m2 = "00000000000000000000000000000000"
            else:
                m2 = "FF000000000000000000000000000000"
            op = "N"
            
            f.write(name + '\n')
            f.write(lt1  + '\n')
            f.write(m1   + '\n')
            f.write(lt2  + '\n')
            f.write(m2   + '\n')
            f.write(op   + '\n')
            f.write("\n")
                

def xor128_dpa():
    fname = "config/xor128_dpa.cfg"
    from server.models import XOR128_Leakage
    with open(fname, "w") as f:
        f.write(XOR128_Leakage.name + "\n")
        
        f.write("Plaintext Byte 0\n")
        f.write("Plaintext\n")
        f.write("FF000000000000000000000000000000\n")
        f.write("Plaintext\n")
        f.write("00000000000000000000000000000000\n")
        f.write("N\n\n")
        
        bit0 = 0x80000000000000000000000000000000
        for i in range(24):
            m = bit0 >> i
            mstr = "{:032x}".format(m)
            f.write("Ciphertext Bit %d\n" % i)
            f.write("Ciphertext\n")
            f.write(mstr + "\n")
            f.write("Ciphertext\n")
            f.write("00000000000000000000000000000000\n")
            f.write("N\n\n")                
                
def xor256_dpa():
    fname = "config/xor256_dpa.cfg"
    from server.models import XOR256_Leakage
    with open(fname, "w") as f:
        f.write(XOR256_Leakage.name + "\n")
        
        f.write("Plaintext Byte 0\n")
        f.write("Plaintext\n")
        f.write("FF00000000000000000000000000000000000000000000000000000000000000\n")
        f.write("Plaintext\n")
        f.write("0000000000000000000000000000000000000000000000000000000000000000\n")
        f.write("N\n\n")
        
        bit0 = 0x8000000000000000000000000000000000000000000000000000000000000000
        for i in range(24):
            m = bit0 >> i
            mstr = "{:064x}".format(m)
            f.write("Ciphertext Bit %d\n" % i)
            f.write("Ciphertext\n")
            f.write(mstr + "\n")
            f.write("Ciphertext\n")
            f.write("0000000000000000000000000000000000000000000000000000000000000000\n")
            f.write("N\n\n")
        
def aes128_iso():
    fname = "config/aes128_iso.cfg"
    from server.models import AES128_Leakage
    with open(fname, "w") as f:
        f.write(AES128_Leakage.name + "\n")
        
        # Test 0: Fixed/random plaintext
        # Note: this should probably be tested separately...
        f.write("Test 0: Fixed/Random Plaintext\n")
        f.write("Plaintext\n")
        f.write("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\n")
        f.write("Plaintext\n")
        f.write("00000000000000000000000000000000\n")
        f.write("E 0xda39a3ee5e6b4b0d3255bfef95601895\n\n")
        
        # Test 1: RIRObitR_i
        for i in range(128):
            m = 0x80000000000000000000000000000000 >> i
            mstr = "%032x" % m
            f.write("Test 1.%d: Round 3 Output to Round 4 Output HD, bit %d\n" % (i, i))
            f.write("Round 3: MixColumns Output\n")
            f.write(mstr + "\n")
            f.write("Round 4: MixColumns Output\n")
            f.write(mstr + "\n")
            f.write("N\n\n")
        
        # Test 2: SoutbitR_i
        for i in range(128):
            m = 0x80000000000000000000000000000000 >> i
            mstr = "%032x" % m
            f.write("Test 2.%d: Round 2 SubBytes Output HW, bit %d\n" % (i, i))
            f.write("Round 2: SubBytes Output\n")
            f.write(mstr + "\n")
            f.write("Round 2: SubBytes Output\n")
            f.write("00000000000000000000000000000000\n")
            f.write("N\n\n")
        
        # Test 3: RoutbitN_i
        for i in range(128):
            m = 0x80000000000000000000000000000000 >> i
            mstr = "%032x" % m
            f.write("Test 3.%d: Round 6 Output HW, bit %d\n" % (i, i))
            f.write("Round 6: MixColumns Output\n")
            f.write(mstr + "\n")
            f.write("Round 6: MixColumns Output\n")
            f.write("00000000000000000000000000000000\n")
            f.write("N\n\n")
        
        # Test 4: Routbyte_N_0_i
        for i in range(128):
            m = 0xFF000000000000000000000000000000
            mstr = "%032x" % m
            f.write("Test 4.%d: Round 1 Output, byte 0 = %d\n" % (i, i))
            f.write("Round 1: MixColumns Output\n")
            f.write(mstr + "\n")
            f.write("Round 1: MixColumns Output\n")
            f.write("00000000000000000000000000000000\n")
            val = i << (128 - 8)
            valstr = "0x%032x" % val
            f.write("E %s\n\n" % valstr)
        
        # Test 5: Routbyte_N_1_i
        for i in range(128):
            m = 0x00FF0000000000000000000000000000
            mstr = "%032x" % m
            f.write("Test 5.%d: Round 1 Output, byte 1 = %d\n" % (i, i))
            f.write("Round 1: MixColumns Output\n")
            f.write(mstr + "\n")
            f.write("Round 1: MixColumns Output\n")
            f.write("00000000000000000000000000000000\n")
            val = i << (128 - 16)
            valstr = "0x%032x" % val
            f.write("E %s\n\n" % valstr)
        
    
if __name__ == "__main__":
    #aes128_brute_force()
    #aes128_simple()
    #aes128_sbox()
    aes128_sbox_dpa()
    aes128_sbox_value()
    #aes256_dec_simple()
    #aes256_bitstream()
    xor128_dpa()
    xor256_dpa()
    aes128_iso()