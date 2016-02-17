/* Wrapper for accessing strings through sequential reads */
function Stream(buf) {
	var position = 0;
	
	function read(length) {
		//var result = buf.toString('utf8', position, position + length);
		var result = buf.slice(position, position + length);
		position += length;
		return result;
	}
	
	/* read a big-endian 32-bit integer */
	function readInt32() {
		var result = buf.readUInt32BE(position);
		position += 4;
		return result;
	}

	/* read a big-endian 16-bit integer */
	function readInt16() {
		var result = buf.readUInt16BE(position);
		position += 2;
		return result;
	}
	
	/* read an 8-bit integer */
	function readInt8(signed) {
        if (signed) {
            var result = buf.readInt8(position);
        } else {
            var result = buf.readUInt8(position);
        }
		position += 1;
		return result;
	}
	
	function eof() {
		return position >= buf.length;
	}
	
	/* read a MIDI-style variable-length integer
		(big-endian value in groups of 7 bits,
		with top bit set to signify that another byte follows)
	*/
	function readVarInt() {
		var result = 0;
		while (true) {
			var b = readInt8();
			if (b & 0x80) {
				result += (b & 0x7f);
				result <<= 7;
			} else {
				/* b is the last byte */
				return result + b;
			}
		}
	}
	
	return {
		'eof': eof,
		'read': read,
		'readInt32': readInt32,
		'readInt16': readInt16,
		'readInt8': readInt8,
		'readVarInt': readVarInt
	}
}
module.exports = Stream;
