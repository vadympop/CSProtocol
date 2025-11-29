-- CSProtocol Wireshark dissector

local csproto = Proto("csprotocol", "CS Sensor Protocol")

local PACKET_CODES = {
    [0] = "SENSOR_REGISTRATION",
    [1] = "SENSOR_DATA",
    [2] = "CHECK_ALIVE_RESPONSE",
    [10] = "REGISTRATION_ACK",
    [11] = "DATA_ACK",
    [12] = "CHECK_ALIVE",
    [28] = "INVALID_CRC",
    [29] = "INVALID_TOKEN",
    [30] = "INVALID_PKT",
}

local FLAG_BITS = {
    LOW_BATTERY = 0x1,
    SENSOR_TYPE = 0x2,
    TOKEN = 0x4,
    PAYLOAD = 0x8,
}

local SENSOR_TYPES = {
    [0] = "TEMP",
    [1] = "WIND",
    [2] = "RAIN",
    [3] = "AIR",
}

local SENSOR_PAYLOADS = {
    TEMP = {
        {name = "temperature", bits = 16, signed = true, scale = 10},
        {name = "humidity", bits = 16, signed = false, scale = 10},
        {name = "dew_point", bits = 16, signed = true, scale = 10},
        {name = "pressure", bits = 32, signed = false, scale = 100},
    },
    WIND = {
        {name = "wind_speed", bits = 16, signed = false, scale = 10},
        {name = "wind_gust", bits = 16, signed = false, scale = 10},
        {name = "wind_direction", bits = 16, signed = false, scale = 1},
        {name = "turbulence", bits = 8, signed = false, scale = 10},
    },
    RAIN = {
        {name = "rainfall", bits = 16, signed = false, scale = 10},
        {name = "soil_moisture", bits = 16, signed = false, scale = 10},
        {name = "packed", bits = 8, kind = "combined", parts = {
            {name = "flood_risk", bits = 2, scale = 1},
            {name = "rain_duration", bits = 6, scale = 1},
        }},
    },
    AIR = {
        {name = "co2", bits = 16, signed = false, scale = 1},
        {name = "ozone", bits = 16, signed = false, scale = 10},
        {name = "air_quality_index", bits = 16, signed = false, scale = 1},
    },
}

local fields = csproto.fields
fields.code = ProtoField.uint8("csprotocol.code", "Packet Code", base.DEC, PACKET_CODES, 0xF0)
fields.flags = ProtoField.uint8("csprotocol.flags", "Flags", base.HEX, nil, 0x0F)
fields.flag_low_battery = ProtoField.bool("csprotocol.flags.low_battery", "Is low battery?", 8, nil, FLAG_BITS.LOW_BATTERY)
fields.flag_sensor_type = ProtoField.bool("csprotocol.flags.sensor_type", "Has sensor type?", 8, nil, FLAG_BITS.SENSOR_TYPE)
fields.flag_token = ProtoField.bool("csprotocol.flags.token", "Has token?", 8, nil, FLAG_BITS.TOKEN)
fields.flag_payload = ProtoField.bool("csprotocol.flags.payload", "Has payload?", 8, nil, FLAG_BITS.PAYLOAD)
fields.timestamp = ProtoField.absolute_time("csprotocol.timestamp", "Timestamp")
fields.crc = ProtoField.uint32("csprotocol.crc", "CRC32", base.HEX)
fields.sensor_type = ProtoField.string("csprotocol.sensor_type", "Sensor Type")
fields.token = ProtoField.uint32("csprotocol.token", "Token")
fields.length = ProtoField.uint16("csprotocol.payload_length", "Payload Length (bits)")
fields.payload = ProtoField.bytes("csprotocol.payload", "Payload")
fields.payload_temperature = ProtoField.float("csprotocol.payload.temperature", "Temperature (°C)")
fields.payload_humidity = ProtoField.float("csprotocol.payload.humidity", "Humidity (%)")
fields.payload_dew_point = ProtoField.float("csprotocol.payload.dew_point", "Dew Point (°C)")
fields.payload_pressure = ProtoField.float("csprotocol.payload.pressure", "Pressure (hPa)")
fields.payload_wind_speed = ProtoField.float("csprotocol.payload.wind_speed", "Wind Speed (m/s)")
fields.payload_wind_gust = ProtoField.float("csprotocol.payload.wind_gust", "Wind Gust (m/s)")
fields.payload_wind_direction = ProtoField.uint16("csprotocol.payload.wind_direction", "Wind Direction (°)")
fields.payload_turbulence = ProtoField.float("csprotocol.payload.turbulence", "Turbulence")
fields.payload_rainfall = ProtoField.float("csprotocol.payload.rainfall", "Rainfall (mm)")
fields.payload_soil_moisture = ProtoField.float("csprotocol.payload.soil_moisture", "Soil Moisture (%)")
fields.payload_flood_risk = ProtoField.uint8("csprotocol.payload.flood_risk", "Flood Risk")
fields.payload_rain_duration = ProtoField.uint8("csprotocol.payload.rain_duration", "Rain Duration (min)")
fields.payload_co2 = ProtoField.uint16("csprotocol.payload.co2", "CO2 (ppm)")
fields.payload_ozone = ProtoField.float("csprotocol.payload.ozone", "Ozone (ppb)")
fields.payload_air_quality = ProtoField.uint16("csprotocol.payload.air_quality_index", "Air Quality Index")

local function to_bits8(n)
    local t = {}
    for i = 7, 0, -1 do
        t[#t+1] = ((n >> i) & 1)
    end
    return table.concat(t)
end

local function bytes_to_bits(tvb)
    local bits = {}
    for i = 0, tvb:len() - 1 do
        bits[#bits +  1] = to_bits8(tvb(i, 1):uint())
    end
    return table.concat(bits)
end

local function range_from_bits(start_bit, bit_len, tvb_len)
    local start_byte = math.floor(start_bit / 8)
    local bit_offset = start_bit % 8
    local total = bit_offset + bit_len
    local byte_len = math.ceil(total / 8)
    if start_byte + byte_len > tvb_len then
        byte_len = tvb_len - start_byte
    end
    if byte_len < 0 then
        byte_len = 0
    end
    return start_byte, byte_len
end

local function bits_to_number(bits_str, signed)
    local value = tonumber(bits_str, 2)
    if not signed then
        return value
    end

    local bit_len = #bits_str
    local limit = 1 << (bit_len - 1)
    if (value & limit) ~= 0 then
        value = value - (1 << bit_len)
    end
    return value
end

local PACKET_STRUCTURE = {
    {name = "code", bits = 4},
    {name = "flags", bits = 4},
    {name = "timestamp", bits = 32},
    {name = "crc", bits = 32},
    {name = "sensor_type", bits = 2, flag = FLAG_BITS.SENSOR_TYPE},
    {name = "token", bits = 32, flag = FLAG_BITS.TOKEN},
    {name = "length", bits = 8, flag = FLAG_BITS.PAYLOAD},
    {name = "payload", bits = -1, flag = FLAG_BITS.PAYLOAD},
}

local function parse_packet(tvb)
    local packet_bits = bytes_to_bits(tvb)
    local total_bits = #packet_bits
    local parsed = {flags = 0}
    local offset = 0

    for _, segment in ipairs(PACKET_STRUCTURE) do
        if segment.flag and (parsed.flags & segment.flag) == 0 then
            if segment.name == "payload" then
                break
            else
                goto continue
            end
        end

        local bits_count = segment.bits
        if bits_count == -1 then
            bits_count = total_bits - offset
        end

        if offset + bits_count > total_bits then
            return nil, string.format("Truncated packet while reading %s", segment.name)
        end

        local bits_slice = packet_bits:sub(offset + 1, offset + bits_count)
        local entry = {
            bits = bits_slice,
            start_bit = offset,
            len_bits = bits_count,
        }

        if segment.name == "payload" then
            entry.value = bits_slice
            parsed[segment.name] = entry
            break
        end

        local value = tonumber(bits_slice, 2)
        entry.value = value
        parsed[segment.name] = entry

        if segment.name == "flags" then
            parsed.flags = value
        elseif segment.name == "sensor_type" then
            entry.type_name = SENSOR_TYPES[value]
        end

        offset = offset + bits_count

        ::continue::
    end

    parsed.total_bits = total_bits
    return parsed
end

local function decode_combined(value, parts)
    local results = {}
    local shift = 0
    for _, part in ipairs(parts) do
        shift = shift + part.bits
    end

    for _, part in ipairs(parts) do
        shift = shift - part.bits
        local mask = (1 << part.bits) - 1
        local data = (value >> shift) & mask
        if part.scale and part.scale > 1 then
            data = data / part.scale
        end
        results[part.name] = data
    end

    return results
end

local function decode_payload(sensor_type, payload_entry, length_entry)
    if not sensor_type or not payload_entry or not length_entry then
        return nil
    end

    local defs = SENSOR_PAYLOADS[sensor_type]
    if not defs then
        return nil
    end

    local bits = payload_entry.bits
    local max_bits = length_entry.value
    if max_bits and max_bits > 0 and max_bits < #bits then
        bits = bits:sub(1, max_bits)
    end

    local offset = 0
    local values = {}
    for _, field in ipairs(defs) do
        if offset + field.bits > #bits then
            break
        end

        local slice = bits:sub(offset + 1, offset + field.bits)
        if field.kind == "combined" then
            local combined_value = tonumber(slice, 2)
            local combined = decode_combined(combined_value, field.parts)
            for name, value in pairs(combined) do
                values[name] = value
            end
        else
            local value = bits_to_number(slice, field.signed)
            if field.scale and field.scale > 1 then
                value = value / field.scale
            end
            values[field.name] = value
        end

        offset = offset + field.bits
    end

    values.__payload_bits = bits
    values.__payload_bit_length = max_bits
    return values
end

local function add_payload_fields(payload_tree, sensor_type, payload_values, payload_entry, tvb)
    if not payload_values then
        return
    end

    local payload_fields = SENSOR_PAYLOADS[sensor_type]
    if not payload_fields then
        return
    end

    local offsets = 0
    for _, field in ipairs(payload_fields) do
        local start_bit = payload_entry.start_bit + offsets
        local bit_len = field.bits
        local start_byte, byte_len = range_from_bits(start_bit, bit_len, tvb:len())
        local range = tvb(start_byte, math.max(byte_len, 0))

        if field.kind == "combined" then
            local combined_value = tonumber(payload_entry.bits:sub(offsets + 1, offsets + field.bits), 2)
            local combined = decode_combined(combined_value, field.parts)
            for _, part in ipairs(field.parts) do
                local name = part.name
                local value = combined[name]
                if name == "flood_risk" then
                    payload_tree:add(fields.payload_flood_risk, range, value)
                elseif name == "rain_duration" then
                    payload_tree:add(fields.payload_rain_duration, range, value)
                end
            end
        else
            local value = payload_values[field.name]
            if value ~= nil then
                if field.name == "temperature" then
                    payload_tree:add(fields.payload_temperature, range, value)
                elseif field.name == "humidity" then
                    payload_tree:add(fields.payload_humidity, range, value)
                elseif field.name == "dew_point" then
                    payload_tree:add(fields.payload_dew_point, range, value)
                elseif field.name == "pressure" then
                    payload_tree:add(fields.payload_pressure, range, value)
                elseif field.name == "wind_speed" then
                    payload_tree:add(fields.payload_wind_speed, range, value)
                elseif field.name == "wind_gust" then
                    payload_tree:add(fields.payload_wind_gust, range, value)
                elseif field.name == "wind_direction" then
                    payload_tree:add(fields.payload_wind_direction, range, value)
                elseif field.name == "turbulence" then
                    payload_tree:add(fields.payload_turbulence, range, value)
                elseif field.name == "rainfall" then
                    payload_tree:add(fields.payload_rainfall, range, value)
                elseif field.name == "soil_moisture" then
                    payload_tree:add(fields.payload_soil_moisture, range, value)
                elseif field.name == "co2" then
                    payload_tree:add(fields.payload_co2, range, value)
                elseif field.name == "ozone" then
                    payload_tree:add(fields.payload_ozone, range, value)
                elseif field.name == "air_quality_index" then
                    payload_tree:add(fields.payload_air_quality, range, value)
                end
            end
        end

        offsets = offsets + field.bits
    end
end

function csproto.dissector(tvb, pinfo, tree)
    pinfo.cols.protocol = "CSPROTO"

    local subtree = tree:add(csproto, tvb())
    local parsed, err = parse_packet(tvb)
    if not parsed then
        subtree:add_expert_info(PI_MALFORMED, PI_ERROR, err)
        return
    end

    local code_entry = parsed.code

    local first_byte = tvb(0, 1)
    if code_entry then
        subtree:add(fields.code, first_byte, code_entry.value)
    end

    if parsed.flags then
        subtree:add(fields.flags, first_byte, parsed.flags)
        local flags_tree = subtree:add(first_byte, "Flags")
        flags_tree:add(fields.flag_low_battery, first_byte, parsed.flags)
        flags_tree:add(fields.flag_sensor_type, first_byte, parsed.flags)
        flags_tree:add(fields.flag_token, first_byte, parsed.flags)
        flags_tree:add(fields.flag_payload, first_byte, parsed.flags)
    end

    if parsed.timestamp then
        local ts_range = tvb(1, 4)
        local timestamp_value = parsed.timestamp.value
        local ts = NSTime(timestamp_value, 0)
        subtree:add(fields.timestamp, ts_range, ts)
    end

    if parsed.crc then
        subtree:add(fields.crc, tvb(5, 4), parsed.crc.value)
    end

    local sensor_type_name = nil
    if parsed.sensor_type then
        sensor_type_name = parsed.sensor_type.type_name or string.format("UNKNOWN (%d)", parsed.sensor_type.value)
        local start_byte, byte_len = range_from_bits(parsed.sensor_type.start_bit, parsed.sensor_type.len_bits, tvb:len())
        subtree:add(fields.sensor_type, tvb(start_byte, byte_len), sensor_type_name)
    end

    if parsed.token then
        local start_byte, byte_len = range_from_bits(parsed.token.start_bit, parsed.token.len_bits, tvb:len())
        subtree:add(fields.token, tvb(start_byte, byte_len), parsed.token.value)
    end

    if parsed.length then
        local start_byte, byte_len = range_from_bits(parsed.length.start_bit, parsed.length.len_bits, tvb:len())
        subtree:add(fields.length, tvb(start_byte, byte_len), parsed.length.value)
    end

    local payload_entry = parsed.payload
    if payload_entry and parsed.length and parsed.length.value > 0 then
        local payload_start_byte, payload_byte_len = range_from_bits(payload_entry.start_bit, parsed.length.value, tvb:len())
        local payload_range = tvb(payload_start_byte, payload_byte_len)
        local payload_tree = subtree:add(fields.payload, payload_range)
        if sensor_type_name then
            payload_tree:set_text(string.format("Payload (%s)", sensor_type_name))
        end

        local payload_values = decode_payload(sensor_type_name, payload_entry, parsed.length)
        add_payload_fields(payload_tree, sensor_type_name, payload_values, payload_entry, tvb)
    end

    local code_name = code_entry and PACKET_CODES[code_entry.value] or "UNKNOWN"
    if sensor_type_name then
        pinfo.cols.info = string.format("%s (%s) - %d bytes", code_name or "UNKNOWN", sensor_type_name, tvb:len())
    else
        pinfo.cols.info = string.format("%s - %d bytes", code_name or "UNKNOWN", tvb:len())
    end
end

local udp_table = DissectorTable.get("udp.port")
for port = 5000, 5005 do
    udp_table:add(port, csproto)
end