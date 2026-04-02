from PIL import Image, ImageDraw, ImageFont

def create_test_invoice():
    img = Image.new("RGB", (600, 800), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    lines = [
        "",
        "  ACME CORPORATION",
        "  123 Business Street, New York, NY 10001",
        "",
        "  ----------------------------------------",
        "  INVOICE",
        "  ----------------------------------------",
        "",
        "  Invoice Number : INV-2024-0042",
        "  Invoice Date   : March 15, 2024",
        "  Due Date       : April 14, 2024",
        "",
        "  Bill To:",
        "  Client Company Ltd",
        "  456 Client Road, Boston MA",
        "",
        "  ----------------------------------------",
        "  DESCRIPTION         QTY    PRICE    TOTAL",
        "  ----------------------------------------",
        "  Web Development      40    $150    $6,000",
        "  UI/UX Design         20    $120    $2,400",
        "  Server Setup          1    $500      $500",
        "  ----------------------------------------",
        "",
        "  Subtotal                            $8,900",
        "  Tax (10%)                             $890",
        "  TOTAL DUE                           $9,790",
        "",
        "  Payment Terms: Net 30",
        "",
    ]

    y = 10
    for line in lines:
        draw.text((0, y), line, fill="black", font=font)
        y += 22

    img.save("test_invoice.jpg")
    print("Created test_invoice.jpg successfully")

create_test_invoice()