import math

class QuatExpand:
    def __init__(self):
        # FormatPrecisionInfo: formatId, baseIndexMask, baseCount, baseSeparation, expandFactorElevenBit, expandFactorTenBit
        self.formats = []
        # formatId table:
        # BINARY2(1111, 1110) = 0xFE
        # BINARY2(1111, 1100) = 0xFC
        # BINARY2(1111, 1000) = 0xF8
        # BINARY2(1111, 0000) = 0xF0
        # BINARY2(1110, 0000) = 0xE0
        # BINARY2(1100, 0000) = 0xC0
        # BINARY2(1000, 0000) = 0x80
        format_ids = [0xFE, 0xFC, 0xF8, 0xF0, 0xE0, 0xC0, 0x80]
        
        self.s_formatData = {} # formatIndex -> (baseValue, expandFactor11, expandFactor10)
        
        for shift in range(7):
            fid = format_ids[shift]
            base_count = 1 << shift
            base_sep = 2.0 / float(base_count + 1)
            half_range = 0.5 * (4.0 / float(base_count + 1))
            
            # 11 bit mask = 0x03FF = 1023? or BINARY3(0011, 1111, 1111) = 0x3FF = 1023
            expand11 = half_range / 1023.0
            # 10 bit mask = 0x01FF = 511
            expand10 = half_range / 511.0
            
            for i in range(base_count):
                fidx = fid | i
                base_val = -1.0 + (i + 1) * base_sep
                self.s_formatData[fidx] = (base_val, expand11, expand10)

    def expand_11bit(self, val, fmt):
        base_val, expand11, _ = self.s_formatData.get(fmt, (0.0, 0.0, 0.0))
        # cs_signBitElevenBit = 0x0400 (bit 10)
        # cs_valueMaskElevenBit = 0x03FF (bits 0-9)
        sign = (val & 0x0400) != 0
        v = val & 0x03FF
        return base_val - (float(v) * expand11) if sign else base_val + (float(v) * expand11)

    def expand_10bit(self, val, fmt):
        base_val, _, expand10 = self.s_formatData.get(fmt, (0.0, 0.0, 0.0))
        # cs_signBitTenBit = 0x0200 (bit 9)
        # cs_valueMaskTenBit = 0x01FF (bits 0-8)
        sign = (val & 0x0200) != 0
        v = val & 0x01FF
        return base_val - (float(v) * expand10) if sign else base_val + (float(v) * expand10)

    def decode_quaternion(self, packed_val, x_fmt, y_fmt, z_fmt):
        # packed format: [MSB] x-11-bit y-11-bit z-10-bit
        # cs_xShift = 21
        # cs_yShift = 10
        val_x = (packed_val >> 21) & 0x07FF
        val_y = (packed_val >> 10) & 0x07FF
        val_z = packed_val & 0x03FF
        
        x = self.expand_11bit(val_x, x_fmt)
        y = self.expand_11bit(val_y, y_fmt)
        z = self.expand_10bit(val_z, z_fmt)
        
        w_sq = 1.0 - (x*x + y*y + z*z)
        w = math.sqrt(max(0.0, w_sq))
        
        # normalize
        length = math.sqrt(x*x + y*y + z*z + w*w)
        if length > 0.0001:
            x /= length
            y /= length
            z /= length
            w /= length
        return (x, y, z, w)

if __name__ == "__main__":
    q = QuatExpand()
    print(f"Decoder initialized with {len(q.s_formatData)} formats.")
    # Test sample
    fmt = list(q.s_formatData.keys())[0]
    res = q.decode_quaternion(0, fmt, fmt, fmt)
    print("Decoded sample zero:", res)

