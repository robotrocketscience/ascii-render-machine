"""Generate a sample gradient image for testing."""

from PIL import Image


def main() -> None:
    width, height = 320, 200
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    assert pixels is not None
    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (1.0 - x / width))
            pixels[x, y] = (r, g, b)
    img.save("examples/sample.jpg", quality=90)
    print("Wrote examples/sample.jpg")


if __name__ == "__main__":
    main()
