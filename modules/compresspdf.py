import streamlit as st
import fitz
import os
import tempfile
import zipfile
import time

from PIL import Image
from io import BytesIO

def save_uploaded_file(uploaded):

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    while True:
        chunk = uploaded.read(1024 * 1024)

        if not chunk:
            break

        temp.write(chunk)

    temp.close()

    return temp.name


def compress_pdf(source, output, quality="medium"):

    doc = fitz.open(source)

    if quality == "high":
        scale = 0.75
        jpg_quality = 85

    elif quality == "medium":
        scale = 0.55
        jpg_quality = 65

    else:
        scale = 0.40
        jpg_quality = 45


    for page in doc:

        images = page.get_images(full=True)

        for img in images:

            xref = img[0]

            pix = fitz.Pixmap(
                doc,
                xref
            )

            if pix.alpha:
                pix = fitz.Pixmap(
                    fitz.csRGB,
                    pix
                )

            image = Image.open(
                BytesIO(
                    pix.tobytes("png")
                )
            )

            new_size = (
                int(image.width * scale),
                int(image.height * scale)
            )

            image = image.resize(
                new_size,
                Image.LANCZOS
            )

            buffer = BytesIO()

            image.save(
                buffer,
                format="JPEG",
                quality=jpg_quality,
                optimize=True
            )

            page.replace_image(
                xref,
                stream=buffer.getvalue()
            )

            pix = None


    doc.save(
        output,
        garbage=4,
        deflate=True,
        clean=True
    )

    doc.close()


def split_pdf(source, limit_mb):

    doc = fitz.open(source)

    progress = st.progress(0)
    status = st.empty()
    parts = []
    current = fitz.open()

    start_time = time.time()

    part = 1

    for index in range(doc.page_count):

        current.insert_pdf(
            doc,
            from_page=index,
            to_page=index
        )

        temp = tempfile.mktemp(
            suffix=".pdf"
        )

        current.save(
            temp,
            garbage=4,
            deflate=True
        )

        size = os.path.getsize(temp) / (1024 * 1024)

        os.remove(temp)

        if size >= limit_mb:

            output = tempfile.mktemp(
                suffix=f"_part_{part}.pdf"
            )

            current.save(
                output,
                garbage=4,
                deflate=True
            )

            parts.append(output)

            current.close()

            current = fitz.open()

            part += 1

            progress.progress(
                (index + 1) / doc.page_count
            )

            elapsed = int(time.time() - start_time)

            status.info(
                f"""
            Splitting PDF...

            Page: {index + 1} / {doc.page_count}

            Creating Part: {part}

            Current size: {size:.2f} MB

            Elapsed time:
            {elapsed // 60:02d}:{elapsed % 60:02d}
            """
            )


    if current.page_count > 0:

        output = tempfile.mktemp(
            suffix=f"_part_{part}.pdf"
        )

        current.save(
            output,
            garbage=4,
            deflate=True
        )

        parts.append(output)

    current.close()
    doc.close()

    return parts


def create_zip(files):

    zip_file = tempfile.mktemp(
        suffix=".zip"
    )

    with zipfile.ZipFile(
        zip_file,
        "w",
        zipfile.ZIP_DEFLATED
    ) as z:

        for file in files:

            z.write(
                file,
                os.path.basename(file)
            )

    return zip_file


def run():

    st.subheader("PDF Compressor and Outlook Splitter")

    uploaded = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    quality = st.selectbox(
        "Compression quality",
        [
            "high",
            "medium",
            "low"
        ],
        index=1
    )


    if uploaded:

        original_size = uploaded.size / (1024 * 1024)

        st.info(
            f"Original size: {original_size:.2f} MB"
        )


        if st.button("Compress Only"):

            source = save_uploaded_file(
                uploaded
            )

            output = tempfile.mktemp(
                suffix="_compressed.pdf"
            )


            with st.spinner(
                "Compressing PDF..."
            ):

                start = time.time()

                compress_pdf(
                    source,
                    output,
                    quality
                )


            new_size = os.path.getsize(output) / (1024 * 1024)

            st.success(
                f"Compressed size: {new_size:.2f} MB | Time: {time.time()-start:.1f}s"
            )


            with open(output,"rb") as f:

                st.download_button(
                    "Download Compressed PDF",
                    f,
                    file_name="compressed.pdf"
                )


        if st.button("Compress + Split for Outlook"):

            limit = st.slider(
                "Maximum part size MB",
                5,
                100,
                15
            )


            source = save_uploaded_file(
                uploaded
            )

            compressed = tempfile.mktemp(
                suffix="_compressed.pdf"
            )


            with st.spinner(
                "Compressing..."
            ):

                compress_pdf(
                    source,
                    compressed,
                    quality
                )


            with st.spinner(
                "Splitting..."
            ):

                parts = split_pdf(
                    compressed,
                    limit
                )


            zip_file = create_zip(
                parts
            )


            st.success(
                f"Created {len(parts)} Outlook files"
            )


            with open(zip_file,"rb") as f:

                st.download_button(
                    "Download ZIP",
                    f,
                    file_name="outlook_pdf_parts.zip"
                )


if __name__ == "__main__":
    run()