import os
import pickle
import random

class VulnerabilityAssessment:
    """
    Kelas ini adalah otak dari simulasi. Bertanggung jawab untuk mengelola
    status server, kerentanan, dan data pemain.
    """
    def __init__(self):
        """
        Saat kelas ini dipanggil, ia akan mencoba memuat status simulasi yang ada.
        Jika tidak ada, ia akan membuat simulasi baru.
        """
        self.state_file = "simulation/assessment_state.p"
        if os.path.exists(self.state_file):
            with open(self.state_file, "rb") as f:
                state = pickle.load(f)
                self.servers = state.get('servers', self._get_default_servers())
                self.scanners = state.get('scanners', {})
                self.last_scans = state.get('last_scans', [])
        else:
            self.reset_simulation()

    def _get_default_servers(self):
        """Mengembalikan konfigurasi server default."""
        return [
            {'name': 'Web Server', 'status': 'UNSCANNED'},
            {'name': 'Database Server', 'status': 'UNSCANNED'},
            {'name': 'Mail Server', 'status': 'UNSCANNED'}
        ]

    def save_state(self):
        """Menyimpan status simulasi saat ini ke dalam file."""
        with open(self.state_file, "wb") as f:
            state = {
                'servers': self.servers, 
                'scanners': self.scanners, 
                'last_scans': self.last_scans
            }
            pickle.dump(state, f)

    def reset_simulation(self):
        """Mereset simulasi ke kondisi awal dengan kerentanan acak."""
        self.servers = self._get_default_servers()
        vulnerabilities = [
            ("CRITICAL", "CRITICAL: SQL Injection"),
            ("MEDIUM", "MEDIUM: Outdated Service"),
            ("SECURE", "SECURE: No Vulnerabilities Found")
        ]
        random.shuffle(vulnerabilities)
        for i, server in enumerate(self.servers):
            server['result_code'], server['result_text'] = vulnerabilities[i]
            server['status'] = 'UNSCANNED'
        self.scanners = {}
        self.last_scans = []
        self.save_state()

    def scan_server(self, server_index, scanner_name):
        """Memproses aksi 'scan' pada server yang dipilih."""
        if not (0 <= server_index < len(self.servers)):
            return None, None
        
        server = self.servers[server_index]
        
        # Hanya proses jika belum pernah discan
        if server['status'] == 'UNSCANNED':
            server['status'] = 'SCANNED'
            
            # Update Top Scanners
            self.scanners.setdefault(scanner_name, 0)
            self.scanners[scanner_name] += 1
            
            # Update Last Scans
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_scans.insert(0, f"`{now}`: **{server['name']}** - Result: `{server['result_code']}` by `{scanner_name}`")
            if len(self.last_scans) > 5: # Batasi hanya 5 log terakhir
                self.last_scans.pop()

            self.save_state()
            
        return server['result_code'], server['result_text']