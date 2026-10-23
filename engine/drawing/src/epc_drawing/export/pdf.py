"""Render a DXF drawing to a PDF page (white background, black/colour lines) with ezdxf + matplotlib.

  python -m epc_drawing.export.pdf <drawing.dxf> <out.pdf>
The page takes the size of the drawing extents (millimetres), so an A1 sheet gives an A1 page.
"""
import sys
from pathlib import Path

MM_PER_INCH = 25.4


def dxf_to_pdf(src: Path, dst: Path) -> Path:
    import ezdxf
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf import bbox
    from ezdxf.addons.drawing import Frontend, RenderContext, config
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    ext = bbox.extents(msp)
    w_mm = max(ext.size.x, 1.0) if ext.has_data else 420.0
    h_mm = max(ext.size.y, 1.0) if ext.has_data else 297.0
    fig = plt.figure(figsize=(w_mm / MM_PER_INCH, h_mm / MM_PER_INCH))
    try:
        ax = fig.add_axes([0, 0, 1, 1])
        cfg = config.Configuration(background_policy=config.BackgroundPolicy.WHITE, color_policy=config.ColorPolicy.COLOR)
        Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=True)
        if ext.has_data:
            ax.set_xlim(ext.extmin.x, ext.extmax.x)
            ax.set_ylim(ext.extmin.y, ext.extmax.y)
        fig.set_size_inches(w_mm / MM_PER_INCH, h_mm / MM_PER_INCH)          # after drawing: the backend may resize the figure
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(dst), format="pdf", facecolor="white")
    finally:
        plt.close(fig)
    return Path(dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print("OK", dxf_to_pdf(Path(sys.argv[1]), Path(sys.argv[2])))
