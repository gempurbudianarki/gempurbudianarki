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
    Fungsi untuk mencari 'slot' di README.md dan menggantinya dengan konten baru.
    """
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("ERROR: README.md tidak ditemukan!")
        sys.exit(1)
        
    marker_begin = f""
    marker_end = f""
    
    # Memastikan kedua penanda ada di file
    if marker_begin not in readme_content or marker_end not in readme_content:
        print(f"ERROR: Penanda {marker_name} tidak ditemukan di README.md!")
        return

    # Meregenerasi konten README
    before_marker = readme_content.split(marker_begin)[0]
    after_marker = readme_content.split(marker_end)[1]
    
    new_readme = f"{before_marker}{marker_begin}\n{new_content}\n{marker_end}{after_marker}"
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)
    print(f"README.md berhasil diupdate untuk marker: {marker_name}")

def main():
    """
    Fungsi utama yang dijalankan oleh GitHub Actions.
    Ini adalah 'Sutradara' dari keseluruhan proses.
    """
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, ISSUE_NUMBER]):
        print("ERROR: Variabel environment (GITHUB_TOKEN, GITHUB_REPOSITORY, ISSUE_NUMBER) tidak di-set!")
        sys.exit(1)
        
    # 1. Menghubungi GitHub API
    repo = Github(GITHUB_TOKEN).get_repo(GITHUB_REPOSITORY)
    issue = repo.get_issue(number=ISSUE_NUMBER)
    issue_author = '@' + issue.user.login
    
    # 2. Memanggil 'Otak'
    assessment = VulnerabilityAssessment()

    # 3. Memahami perintah dari judul issue
    issue_title = issue.title
    
    # Jika perintahnya adalah reset
    if issue_title == "VA: Reset Simulation":
        if issue.user.login == GITHUB_REPOSITORY.split('/')[0]: # Hanya pemilik repo yang bisa reset
            assessment.reset_simulation()
            issue.create_comment("Sistem simulasi berhasil di-reset. Kerentanan baru telah digenerate secara acak.")
            print("Simulasi di-reset oleh pemilik repositori.")
        else:
            issue.create_comment("Gagal: Hanya pemilik repositori yang dapat me-reset simulasi.")
            issue.edit(state='closed', labels=['Invalid'])
            print("Percobaan reset gagal oleh non-pemilik.")
            return

    # Jika perintahnya adalah scan
    else:
        match = re.search(r'VA: Run Scan on (Web Server|Database Server|Mail Server)', issue_title)
        if match:
            server_name = match.group(1)
            server_map = {"Web Server": 0, "Database Server": 1, "Mail Server": 2}
            server_index = server_map.get(server_name)
            
            result_code, result_text = assessment.scan_server(server_index, issue_author)
            
            # Memberi respons di issue
            issue.create_comment(f"Terima kasih {issue_author} telah berpartisipasi! Hasil scan pada **{server_name}**: `{result_text}`")
            issue.edit(state='closed', labels=[f"Status: {result_code}"])
            print(f"Scan berhasil diproses untuk {server_name}.")
        else:
            issue.create_comment("Perintah tidak dikenali. Pastikan judul issue sesuai format.")
            issue.edit(state='closed', labels=['Invalid'])
            print(f"Perintah tidak dikenali: {issue_title}")
            return

    # 4. Memanggil 'Tangan Seniman' untuk menggambar semua bagian
    board_md = markdown_generator.generate_va_board(assessment)
    last_scans_md = markdown_generator.generate_last_scans(assessment)
    top_operators_md = markdown_generator.generate_top_operators(assessment)
    
    # 5. Mengupdate README
    replace_in_readme('VA_BOARD', board_md)
    replace_in_readme('LAST_SCANS', last_scans_md)
    replace_in_readme('TOP_OPERATORS', top_operators_md)

if __name__ == "__main__":
    main()