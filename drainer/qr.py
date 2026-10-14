import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from PIL import Image

LINK = "https://trustwalletxrr.netlify.app"   # apna link
LOGO = "logo.png"                              # apna logo

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=14, border=2)
qr.add_data(LINK)
qr.make(fit=True)

img = qr.make_image(
    image_factory=StyledPilImage,
    module_drawer=RoundedModuleDrawer(),
    color_mask=RadialGradiantColorMask(
        back_color=(255,255,255),
        center_color=(5,0,255),
        edge_color=(51,117,187)
    )
).convert("RGB")

# logo beech me
logo = Image.open(LOGO).convert("RGBA")
size = int(img.size[0] * 0.22)
logo = logo.resize((size, size), Image.LANCZOS)

# gol white ring
from PIL import ImageDraw
pad = int(size * 0.14)
ring = Image.new("RGBA", (size + pad*2, size + pad*2), (255,255,255,255))
mask = Image.new("L", (size + pad*2, size + pad*2), 0)
ImageDraw.Draw(mask).ellipse((0,0,size+pad*2,size+pad*2), fill=255)
ring.putalpha(mask)
ring.paste(logo, (pad, pad), logo)

pos = ((img.size[0]-ring.size[0])//2, (img.size[1]-ring.size[1])//2)
img.paste(ring, pos, ring)

img.save("page_qr.png")
print("✅ Ban gaya: page_qr.png")