import pandas as pd
import streamlit as st
import zipfile
from io import BytesIO

def run():

    st.subheader("# 📄 PDF Batch Splitter (ZIP Upload Mode)")

    uploaded_zip = st.file_uploader(
        "Upload ZIP file containing PDFs",
        type=["zip"]
    )

    st.markdown("---")
    st.caption("© 2026 ACB Toolkit | Developed by IT Department")

    max_size_mb = st.number_input("Max folder size (MB)", value=20)
    max_size = max_size_mb * 1024 * 1024

    if uploaded_zip:
        with zipfile.ZipFile(uploaded_zip) as z:
            pdf_files = []

            for name in z.namelist():
                if name.lower().endswith(".pdf"):
                    data = z.read(name)
                    file_obj = BytesIO(data)
                    file_obj.name = name.split("/")[-1]
                    file_obj.size = len(data)
                    pdf_files.append(file_obj)

        if not pdf_files:
            st.error("No PDF files found in ZIP.")
            return

        total_size = sum(f.size for f in pdf_files) / (1024 * 1024)
        st.info(f"Total extracted size: {total_size:.2f} MB")

        # 🔽 SAME LOGIC STARTS HERE
        files = sorted(pdf_files, key=lambda x: x.size, reverse=True)

        batches = []
        current_batch = []
        current_size = 0
        folder_index = 1

        for file in files:
            if file.size > max_size:
                st.warning(f"{file.name} exceeds max size and will be placed alone.")

            if (current_size + file.size) > max_size:
                batches.append((folder_index, current_batch))
                folder_index += 1
                current_batch = []
                current_size = 0

            current_batch.append(file)
            current_size += file.size

        if current_batch:
            batches.append((folder_index, current_batch))

        st.success(f"✅ {len(batches)} batch folders created")

        # 📦 ZIP OUTPUT
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for folder_index, batch in batches:
                for file in batch:
                    file.seek(0)
                    zip_file.writestr(
                        f"Batch_{folder_index}/{file.name}",
                        file.read()
                    )

        st.download_button(
            label="⬇️ Download All Batches (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="PDF_Batches.zip",
            mime="application/zip"
        )

        # 📊 Tabs UI (same as before)
        st.markdown("## 📊 View Batch Details")

        tab_labels = [
            f"Batch_{folder_index} ({len(batch)} files)"
            for folder_index, batch in batches
        ]

        tabs = st.tabs(tab_labels)

        for i, tab in enumerate(tabs):
            folder_index, batch = batches[i]
            total_mb = sum(f.size for f in batch) / (1024 * 1024)

            with tab:
                st.write(f"### 📦 Batch_{folder_index}")
                st.write(f"**{len(batch)} files — {total_mb:.2f} MB**")

                st.divider()

                for f in batch:
                    st.write(f"• {f.name}")