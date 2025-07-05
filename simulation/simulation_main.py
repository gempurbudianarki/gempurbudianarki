# =====================================================================================
# == VERSI FINAL LENGKAP - simulation_main.py ==
# =====================================================================================

import os
import re
import sys
from github import Github
from assessment_logic import VulnerabilityAssessment
import markdown_generator

# Variabel global untuk keamanan, akan diisi oleh GitHub Actions
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY')
ISSUE_NUMBER = int(os.environ.get('ISSUE_NUMBER'))

def replace_in_readme(marker_name, new_content):
    """
    Fungsi baru yang lebih kuat untuk mencari 'slot' di README.md dan menggantinya.
    Menggunakan Regular Expressions (regex) untuk presisi maksimal.
    """
    try:
        with open('README.md', 'r+', encoding='utf-8') as f:
            readme_content = f.read()

            marker_begin = f""
            marker_end = f""
            pattern = re.compile(f"({re.escape(marker_begin)})(.*?)({re.escape(marker_end)})", re.DOTALL)

            replacement = f"\n{new_content}\n"
            full_replacement_block = f"\\1{replacement}\\3"

            new_readme, count = pattern.subn(full_replacement_block, readme_content)

            if count > 0:
                f.seek(0)
                f.truncate()
                f.write(new_readme)
                print(f"README.md berhasil diupdate untuk marker: {marker_name}")
            else:
                print(f"ERROR: Penanda {marker_name} tidak ditemukan di README.md! Tidak ada perubahan yang dilakukan.")

    except FileNotFoundError:
        print("ERROR: README.md tidak ditemukan!")
        sys.exit(1)

def main():
    """
    Fungsi utama yang dijalankan oleh GitHub Actions.
    """
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, ISSUE_NUMBER]):
        print("ERROR: Variabel environment tidak di-set!")
        sys.exit(1)

    repo = Github(GITHUB_TOKEN).get_repo(GITHUB_REPOSITORY)
    issue = repo.get_issue(number=ISSUE_NUMBER)
    issue_author = '@' + issue.user.login

    assessment = VulnerabilityAssessment()
    issue_title = issue.title

    if issue_title == "VA: Reset Simulation":
        if issue.user.login == GITHUB_REPOSITORY.split('/')[0]:
            assessment.reset_simulation()
            issue.create_comment("Sistem simulasi berhasil di-reset. Kerentanan baru telah digenerate secara acak.")
            print("Simulasi di-reset oleh pemilik repositori.")
        else:
            issue.create_comment("Gagal: Hanya pemilik repositori yang dapat me-reset simulasi.")
            print("Percobaan reset gagal oleh non-pemilik.")
    else:
        match = re.search(r'VA: Run Scan on (Web Server|Database Server|Mail Server)', issue_title)
        if match:
            server_name = match.group(1)
            server_map = {"Web Server": 0, "Database Server": 1, "Mail Server": 2}
            server_index = server_map.get(server_name)

            result_code, result_text = assessment.scan_server(server_index, issue_author)

            issue.create_comment(f"Terima kasih {issue_author} telah berpartisipasi! Hasil scan pada **{server_name}**: `{result_text}`")
            issue.edit(state='closed', labels=[f"Status: {result_code}"])
            print(f"Scan berhasil diproses untuk {server_name}.")
        else:
            issue.create_comment("Perintah tidak dikenali. Pastikan judul issue sesuai format.")
            print(f"Perintah tidak dikenali: {issue_title}")

    board_md = markdown_generator.generate_va_board(assessment)
    last_scans_md = markdown_generator.generate_last_scans(assessment)
    top_operators_md = markdown_generator.generate_top_operators(assessment)

    replace_in_readme('VA_BOARD', board_md)
    replace_in_readme('LAST_SCANS', last_scans_md)
    replace_in_readme('TOP_OPERATORS', top_operators_md)

    if issue.state == 'open':
        issue.edit(state='closed')

if __name__ == "__main__":
    main()