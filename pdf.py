import os
import fitz  
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QScrollArea,
    QFrame,
    QMessageBox,
    QGridLayout,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyPDF2 import PdfMerger

# ----- Initialize App -----
app = QApplication([])
main_window = QWidget()
main_window.setWindowTitle("PDF Tool")
main_window.resize(1200, 700)

main_layout = QVBoxLayout()
btn_row = QHBoxLayout()

# Buttons
add_pdf = QPushButton("Add PDF")
clear_pdf = QPushButton("Clear All")
merge_pdf = QPushButton("Merge PDFs")
theme_toggle = QPushButton("🌙 Dark Mode")
remove_page_btn = QPushButton("Remove PDF Pages")
apply_removal_btn = QPushButton("Apply Page Removal")
apply_removal_btn.hide()

theme_toggle.setCheckable(True)
btn_row.addWidget(remove_page_btn)
btn_row.addWidget(apply_removal_btn)
btn_row.addWidget(add_pdf)
btn_row.addWidget(clear_pdf)
btn_row.addWidget(merge_pdf)
btn_row.addWidget(theme_toggle)
main_layout.addLayout(btn_row)

# Styles
light_mode_stylesheet = """ QWidget { background-color: #f0f0f0; color: #000; font-family: 'Segoe UI'; }
QFrame { background-color: white; border: 1px solid #ccc; border-radius: 12px; }
QPushButton { background-color: #3498db; color: white; padding: 8px 15px; border: none; border-radius: 8px;font:18px;font-weight:700; }
QPushButton:hover { background-color: #2980b9; }
QPushButton:pressed { background-color: #2471a3; } """
dark_mode_stylesheet = """ QWidget { background-color: #121212; color: #f0f0f0; font-family: 'Segoe UI'; }
QFrame { background-color: #1e1e1e; border: 1px solid #444; border-radius: 12px; }
QPushButton { background-color: #2c2c2c; color: #f0f0f0; padding: 6px 12px; border: none; border-radius: 8px; }
QPushButton:hover { background-color: #3c3c3c; } """


def toggle_theme():
    if theme_toggle.isChecked():
        app.setStyleSheet(dark_mode_stylesheet)
        theme_toggle.setText("☀️ Light Mode")
    else:
        app.setStyleSheet(light_mode_stylesheet)
        theme_toggle.setText("🌙 Dark Mode")


theme_toggle.clicked.connect(toggle_theme)

# PDF Grid placing pdfs in rows
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_widget = QWidget()
pdf_layout = QGridLayout()
scroll_widget.setLayout(pdf_layout)
scroll_area.setWidget(scroll_widget)
main_layout.addWidget(scroll_area)

merge_pdf_list = []
selected_pages = set()
pdf_for_removal_path = ""


# updating pdf lst location when selecting them
def update_pdf_list():
    for i in reversed(range(pdf_layout.count())):
        widget = pdf_layout.itemAt(i).widget()
        if widget:
            widget.setParent(None)
    for index, path in enumerate(merge_pdf_list):
        card = QFrame()
        card.setFixedSize(200, 200)
        card.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #ddd; border-radius: 12px; }"
        )
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(10, 10, 10, 10)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 12px; } QPushButton:hover { background-color: #c0392b; }"
        )
        remove_btn.clicked.connect(lambda _, p=path: remove_pdf(p))
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(remove_btn)

        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 36px;")
        icon_label.setAlignment(Qt.AlignCenter)

        name_label = QLabel(os.path.basename(path))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)

        card_layout.addLayout(top_bar)
        card_layout.addWidget(icon_label)
        card_layout.addWidget(name_label)
        card.setLayout(card_layout)
        pdf_layout.addWidget(card, index // 3, index % 3)


# Add PDF to list
def select_file():
    files, _ = QFileDialog.getOpenFileNames(
        main_window, "Select PDFs", "", "PDF Files (*.pdf)"
    )
    for file in files:
        if file not in merge_pdf_list:
            merge_pdf_list.append(file)
    update_pdf_list()


# Remove file
def remove_pdf(file_path):
    if file_path in merge_pdf_list:
        merge_pdf_list.remove(file_path)
        update_pdf_list()


# Clear All
def clear_all_pdfs():
    merge_pdf_list.clear()
    update_pdf_list()


# Merge PDFs
def merge_pdfs():
    if len(merge_pdf_list) < 2:
        QMessageBox.warning(main_window, "Error", "Add at least two PDFs to merge.")
        return
    save_path, _ = QFileDialog.getSaveFileName(
        main_window, "Save Merged PDF", "", "PDF Files (*.pdf)"
    )
    if not save_path:
        return
    merger = PdfMerger()
    try:
        for pdf in merge_pdf_list:
            merger.append(pdf)
        merger.write(save_path)
        QMessageBox.information(main_window, "Success", f"Saved to: {save_path}")
    except Exception as e:
        QMessageBox.critical(main_window, "Error", str(e))
    finally:
        merger.close()


# Show PDF pages to remove
def show_pdf_thumbnails():
    global pdf_for_removal_path, selected_pages
    selected_pages = set()
    pdf_for_removal_path, _ = QFileDialog.getOpenFileName(
        main_window, "Select PDF", "", "PDF Files (*.pdf)"
    )
    if not pdf_for_removal_path:
        return
    doc = fitz.open(pdf_for_removal_path)

    # Clear layout
    for i in reversed(range(pdf_layout.count())):
        widget = pdf_layout.itemAt(i).widget()
        if widget:
            widget.setParent(None)

    # Show thumbnails
    def make_toggle(index, label):
        def toggle(event):
            if index in selected_pages:
                selected_pages.remove(index)
                label.setStyleSheet("border: 2px solid transparent; opacity: 1;")
            else:
                selected_pages.add(index)
                label.setStyleSheet("border: 2px solid red; opacity: 0.4;")

        return toggle

    thumb_size_w, thumb_size_h = 220, 280  # bigger size for better visibility
    columns = 4  # 4 images per row

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # zoom for quality
        mode = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, mode)
        pixmap = QPixmap.fromImage(img)
        thumb = QLabel()
        thumb.setPixmap(pixmap)
        thumb.setFixedSize(thumb_size_w, thumb_size_h)
        thumb.setScaledContents(True)
        thumb.setStyleSheet("border: 2px solid transparent;")

        thumb.mousePressEvent = make_toggle(i, thumb)

        pdf_layout.addWidget(thumb, i // columns, i % columns)

    doc.close()
    apply_removal_btn.show()



# Remove selected pages and save
def remove_selected_pages():
    if not pdf_for_removal_path or not selected_pages:
        return
    doc = fitz.open(pdf_for_removal_path)
    new_doc = fitz.open()
    for i in range(len(doc)):
        if i not in selected_pages:
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
    save_path, _ = QFileDialog.getSaveFileName(
        main_window, "Save Edited PDF", "", "PDF Files (*.pdf)"
    )
    if save_path:
        new_doc.save(save_path)
        QMessageBox.information(
            main_window,
            "Done",
            f"Saved PDF with {len(selected_pages)} page(s) removed.",
        )
    new_doc.close()
    doc.close()
    apply_removal_btn.hide()
    update_pdf_list()


# Connect
add_pdf.clicked.connect(select_file)
clear_pdf.clicked.connect(clear_all_pdfs)
merge_pdf.clicked.connect(merge_pdfs)
remove_page_btn.clicked.connect(show_pdf_thumbnails)
apply_removal_btn.clicked.connect(remove_selected_pages)

apply_removal_btn.setStyleSheet("QPushButton {background-color:red;font-weight:700;}")

# executing the app display
main_window.setLayout(main_layout)
app.setStyleSheet(light_mode_stylesheet)
main_window.show()
app.exec_()
