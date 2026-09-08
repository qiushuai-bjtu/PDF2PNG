import subprocess
import shutil
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog


def select_pdf():
    """弹窗选择 PDF 文件。"""
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="选择 PDF 文件",
        filetypes=[
            ("PDF 文件", "*.pdf"),
            ("所有文件", "*.*"),
        ],
    )

    root.destroy()
    return file_path


def select_output_dir():
    """弹窗选择 PNG 输出目录。"""
    root = tk.Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(
        title="选择 PNG 输出文件夹"
    )

    root.destroy()
    return folder_path


def get_pdf_page_count(pdf_path):
    """
    使用 pdfinfo 获取 PDF 总页数。
    pdfinfo 与 pdftoppm 都属于 Poppler。
    """
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())

    raise RuntimeError("无法读取 PDF 页数。")


def parse_pages(page_input, total_pages):
    """
    解析页面输入。

    支持：
        1
        1-5
        1,3,5
        1-3,7
        all
    """
    page_input = page_input.strip().lower()

    if page_input == "all":
        return list(range(1, total_pages + 1))

    pages = set()

    for part in page_input.split(","):
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start_text, end_text = part.split("-", 1)

            start = int(start_text)
            end = int(end_text)

            if start > end:
                raise ValueError(
                    f"页面范围错误：{start}-{end}"
                )

            pages.update(range(start, end + 1))

        else:
            pages.add(int(part))

    if not pages:
        raise ValueError("没有指定有效页面。")

    pages = sorted(pages)

    for page in pages:
        if page < 1 or page > total_pages:
            raise ValueError(
                f"第 {page} 页超出范围。"
                f"该 PDF 共 {total_pages} 页。"
            )

    return pages


def convert_page(pdf_path, page_number, dpi, output_dir):
    """使用 pdftoppm 将指定页面转换为 PNG。"""

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    # 临时输出前缀
    output_prefix = (
        output_dir
        / f"{pdf_path.stem}_page_{page_number:03d}"
    )

    command = [
        "pdftoppm",
        "-f", str(page_number),
        "-l", str(page_number),
        "-r", str(dpi),
        "-png",
        "-singlefile",
        str(pdf_path),
        str(output_prefix),
    ]

    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    return output_prefix.with_suffix(".png")


def check_poppler():
    """检查 Poppler 是否安装。"""

    missing = []

    if shutil.which("pdftoppm") is None:
        missing.append("pdftoppm")

    if shutil.which("pdfinfo") is None:
        missing.append("pdfinfo")

    if missing:
        print("\n错误：没有找到 Poppler。")
        print("缺少：", ", ".join(missing))

        print("\nUbuntu / Debian 请运行：")
        print("sudo apt install poppler-utils")

        sys.exit(1)


def main():

    print("=" * 55)
    print("             PDF → PNG 高清转换工具")
    print("=" * 55)

    # --------------------------------------------------
    # 0. 检查 Poppler
    # --------------------------------------------------

    check_poppler()

    # --------------------------------------------------
    # 1. 选择 PDF
    # --------------------------------------------------

    print("\n请选择 PDF 文件...")

    pdf_path = select_pdf()

    if not pdf_path:
        print("\n未选择 PDF，程序退出。")
        return

    pdf_path = Path(pdf_path)

    print(f"\n已选择：")
    print(pdf_path)

    # --------------------------------------------------
    # 2. 获取 PDF 信息
    # --------------------------------------------------

    try:
        total_pages = get_pdf_page_count(pdf_path)

    except Exception as e:
        print(f"\n读取 PDF 失败：{e}")
        return

    print(f"\nPDF 总页数：{total_pages}")

    # --------------------------------------------------
    # 3. 输入页面
    # --------------------------------------------------

    print("\n页面输入示例：")
    print("  1          → 第 1 页")
    print("  1-5        → 第 1 至 5 页")
    print("  1,3,5      → 第 1、3、5 页")
    print("  1-3,7      → 第 1 至 3 页和第 7 页")
    print("  all        → 全部页面")

    while True:

        page_input = input(
            "\n请输入需要转换的页面："
        ).strip()

        try:
            pages = parse_pages(
                page_input,
                total_pages
            )
            break

        except Exception as e:
            print(f"页面输入错误：{e}")

    # --------------------------------------------------
    # 4. 输入 DPI
    # --------------------------------------------------

    while True:

        dpi_input = input(
            "\n请输入输出 DPI [默认 300]："
        ).strip()

        # 直接回车
        if not dpi_input:
            dpi = 300
            break

        try:
            dpi = int(dpi_input)

            if dpi <= 0:
                raise ValueError

            break

        except ValueError:
            print("请输入有效的正整数 DPI。")

    # --------------------------------------------------
    # 5. 选择输出目录
    # --------------------------------------------------

    print("\n请选择 PNG 输出文件夹...")

    output_dir = select_output_dir()

    if not output_dir:
        print("\n未选择输出目录，程序退出。")
        return

    output_dir = Path(output_dir)

    print(f"\n输出目录：")
    print(output_dir)

    # --------------------------------------------------
    # 6. 转换
    # --------------------------------------------------

    print("\n" + "-" * 55)

    print(
        f"开始转换：{len(pages)} 页，"
        f"{dpi} DPI"
    )

    print("-" * 55)

    success = 0

    for index, page_number in enumerate(
        pages,
        start=1
    ):

        print(
            f"[{index}/{len(pages)}] "
            f"正在转换第 {page_number} 页...",
            end=" "
        )

        try:

            output_file = convert_page(
                pdf_path,
                page_number,
                dpi,
                output_dir
            )

            print("完成")

            success += 1

        except subprocess.CalledProcessError as e:

            print("失败")

            if e.stderr:
                print(e.stderr)

    # --------------------------------------------------
    # 7. 完成
    # --------------------------------------------------

    print("\n" + "=" * 55)

    print("转换完成")

    print(f"成功：{success}/{len(pages)} 页")

    print(f"\nPNG 保存位置：")
    print(output_dir)

    print("=" * 55)


if __name__ == "__main__":
    main()