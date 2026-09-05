import io
import json
import base64
import qrcode
import qrcode.image.svg


def generate_qr_svg(payload_text: str) -> str:
    """
    Generates a standalone SVG QR code containing raw string or JSON payload.
    """
    factory = qrcode.image.svg.SvgPathImage
    qr_img = qrcode.make(
        payload_text,
        image_factory=factory,
        box_size=10,
        border=2
    )
    stream = io.BytesIO()
    qr_img.save(stream)
    return stream.getvalue().decode('utf-8')


def generate_trip_qr_svg(
    shipment_code: str,
    qr_token: str,
    origin: str = "",
    destination: str = "",
    cargo_type: str = "",
    priority: str = ""
) -> str:
    """
    Generates a standalone SVG QR code containing the trip activation payload.
    Used by drivers to scan and activate corridor trips in the Field Driver PWA.
    """
    payload = {
        "app": "ResQRoute-MDoNER",
        "shipment_code": shipment_code,
        "token": qr_token,
        "origin": origin,
        "destination": destination,
        "cargo": cargo_type,
        "priority": priority
    }
    qr_string = json.dumps(payload, separators=(',', ':'))
    return generate_qr_svg(qr_string)


def generate_qr_data_url(svg_string: str) -> str:
    """
    Wraps raw SVG in a base64 Data URL for safe embedding in <img> or CSS.
    """
    b64 = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"
