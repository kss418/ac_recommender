const MAGIC = '\x93NUMPY'

const DTYPE_READERS = {
  f4: { bytes: 4, read: (view, offset, littleEndian) => view.getFloat32(offset, littleEndian) },
  f8: { bytes: 8, read: (view, offset, littleEndian) => view.getFloat64(offset, littleEndian) },
  i1: { bytes: 1, read: (view, offset) => view.getInt8(offset) },
  u1: { bytes: 1, read: (view, offset) => view.getUint8(offset) },
  i2: { bytes: 2, read: (view, offset, littleEndian) => view.getInt16(offset, littleEndian) },
  u2: { bytes: 2, read: (view, offset, littleEndian) => view.getUint16(offset, littleEndian) },
  i4: { bytes: 4, read: (view, offset, littleEndian) => view.getInt32(offset, littleEndian) },
  u4: { bytes: 4, read: (view, offset, littleEndian) => view.getUint32(offset, littleEndian) },
}

export function parseNpy(buffer) {
  const bytes = new Uint8Array(buffer)
  const magic = ascii(bytes, 0, 6)
  if (magic !== MAGIC) {
    throw new Error('Invalid .npy file: magic header mismatch')
  }

  const major = bytes[6]
  const minor = bytes[7]
  const view = new DataView(buffer)
  const headerLengthBytes = major <= 1 ? 2 : 4
  const headerLength =
    headerLengthBytes === 2 ? view.getUint16(8, true) : view.getUint32(8, true)
  const headerOffset = 8 + headerLengthBytes
  const dataOffset = headerOffset + headerLength
  const header = decodeHeader(bytes.slice(headerOffset, dataOffset), major)
  const descriptor = parseHeader(header)
  const dtype = parseDescr(descriptor.descr)
  const elementCount = descriptor.shape.reduce((product, value) => product * value, 1)
  const dataBytes = elementCount * dtype.bytes

  if (dataOffset + dataBytes > buffer.byteLength) {
    throw new Error('Invalid .npy file: data section is shorter than declared shape')
  }

  return {
    buffer,
    version: `${major}.${minor}`,
    header,
    dataOffset,
    dataBytes,
    descr: descriptor.descr,
    dtype: dtype.label,
    dtypeCode: dtype.code,
    dtypeBytes: dtype.bytes,
    littleEndian: dtype.littleEndian,
    fortranOrder: descriptor.fortranOrder,
    shape: descriptor.shape,
  }
}

export function readNpyValues(npyInfo, rowIndex = 0, limit = 8) {
  if (npyInfo.fortranOrder) {
    throw new Error('Fortran-order vector preview is not implemented')
  }
  if (npyInfo.shape.length < 1) return []

  const rows = npyInfo.shape[0]
  if (rowIndex < 0 || rowIndex >= rows) {
    throw new Error(`Row index ${rowIndex} is outside vector range`)
  }

  const reader = DTYPE_READERS[npyInfo.dtypeCode]
  if (!reader) {
    throw new Error(`Vector preview does not support dtype ${npyInfo.descr}`)
  }

  const rowWidth = npyInfo.shape.slice(1).reduce((product, value) => product * value, 1) || 1
  const count = Math.min(limit, rowWidth)
  const rowOffset = npyInfo.dataOffset + rowIndex * rowWidth * npyInfo.dtypeBytes
  const view = new DataView(npyInfo.buffer)

  return Array.from({ length: count }, (_, index) => {
    const offset = rowOffset + index * npyInfo.dtypeBytes
    const value = reader.read(view, offset, npyInfo.littleEndian)
    return Number.isFinite(value) ? Number(value.toFixed(6)) : value
  })
}

function parseHeader(header) {
  const descr = matchString(header, /'descr'\s*:\s*'([^']+)'/)
  const fortranOrder = matchBoolean(header, /'fortran_order'\s*:\s*(True|False)/)
  const shapeText = matchString(header, /'shape'\s*:\s*\(([^)]*)\)/)
  const shape = shapeText
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => Number.parseInt(part, 10))

  if (!descr || !shape.length || shape.some((value) => !Number.isFinite(value))) {
    throw new Error('Invalid .npy header: missing descr or shape')
  }

  return { descr, fortranOrder, shape }
}

function parseDescr(descr) {
  const endian = descr[0]
  const code = descr.slice(1)
  const reader = DTYPE_READERS[code]
  if (!reader) {
    return {
      code,
      bytes: Number.parseInt(code.slice(1), 10) || 1,
      label: descr,
      littleEndian: endian !== '>',
    }
  }

  const kind = {
    f: 'float',
    i: 'int',
    u: 'uint',
  }[code[0]]

  return {
    code,
    bytes: reader.bytes,
    label: `${kind}${reader.bytes * 8}`,
    littleEndian: endian !== '>',
  }
}

function matchString(text, regex) {
  const match = text.match(regex)
  return match?.[1] ?? ''
}

function matchBoolean(text, regex) {
  return matchString(text, regex) === 'True'
}

function decodeHeader(bytes, major) {
  if (major >= 3) {
    return new TextDecoder('utf-8').decode(bytes).trim()
  }
  return new TextDecoder('latin1').decode(bytes).trim()
}

function ascii(bytes, start, end) {
  return String.fromCharCode(...bytes.slice(start, end))
}
