import requests
import time
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

TOTAL_REQUESTS = 30
CONCURRENCY = 10
LB_URL = "http://localhost:8080/"

NGINX_CONF = {
    "round_robin": """events {
    worker_connections 1024;
}
http {
    upstream sicepat-backend {
        server backend-checkout:8000;
        server backend-katalog:8000;
        server backend-cart:8000;
    }
    server {
        listen 80;
        location / {
            proxy_pass http://sicepat-backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}""",
    "least_conn": """events {
    worker_connections 1024;
}
http {
    upstream sicepat-backend {
        least_conn;
        server backend-checkout:8000;
        server backend-katalog:8000;
        server backend-cart:8000;
    }
    server {
        listen 80;
        location / {
            proxy_pass http://sicepat-backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}""",
}

def set_nginx_mode(mode):
    conf = NGINX_CONF[mode]
    with open("nginx.conf", "w") as f:
        f.write(conf)
    subprocess.run(["docker", "compose", "restart", "nginx"], check=True, capture_output=True)

def send_request(req_id):
    try:
        start = time.time()
        resp = requests.get(LB_URL, timeout=30)
        elapsed = time.time() - start
        data = resp.json() if resp.status_code == 200 else {"server": "error"}
        return {"req_id": req_id, "server": data.get("server"), "delay": data.get("delay"), "time": elapsed}
    except Exception:
        return {"req_id": req_id, "server": "timeout", "delay": None, "time": None}

def run_test(algorithm_name):
    print(f"\n{'=' * 50}")
    print(f"  UJI COBA: {algorithm_name}")
    print(f"{'=' * 50}")

    all_results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(send_request, i) for i in range(TOTAL_REQUESTS)]
        for f in as_completed(futures):
            all_results.append(f.result())

    total_time = time.time() - start_time
    all_results.sort(key=lambda x: x["req_id"])

    server_count = Counter(r["server"] for r in all_results)
    errors = server_count.get("timeout", 0) + server_count.get("error", 0)

    print(f"\nDistribusi Request:")
    print(f"  Server Checkout (slow): {server_count.get('checkout', 0)} request")
    print(f"  Server Katalog  (fast): {server_count.get('katalog', 0)} request")
    print(f"  Server Cart     (fast): {server_count.get('cart', 0)} request")
    print(f"  Error/Timeout         : {errors} request")
    print(f"\nTotal waktu selesai: {total_time:.2f} detik")

    if errors > 0:
        print(f"\n⚠️  Ada {errors} request gagal — mungkin container belum siap.")

    print(f"\nUrutan Request (req_id -> server):")
    for r in all_results:
        mark = " <- check this" if r["server"] == "checkout" else ""
        t = r["time"] if r["time"] is not None else 0.0
        server = r["server"] if r["server"] else "error"
        print(f"  Req {r['req_id']:2d} -> {server:10s} ({t:.2f}s){mark}")

    return {"algorithm": algorithm_name, "total_time": total_time, "distribution": dict(server_count)}

def main():
    parser = argparse.ArgumentParser(description="SiCepat Load Balancer Test")
    parser.add_argument("mode", nargs="?", choices=["1", "2", "both"],
                        help="1=Round Robin, 2=Least Connections, both=keduanya")
    args = parser.parse_args()

    if args.mode == "both":
        print("\nMode BOTH: jalankan Round Robin dulu, lalu Least Connections")
        input("\nTekan Enter untuk mulai Round Robin...")
        set_nginx_mode("round_robin")
        print("\nMode: ROUND ROBIN")
        time.sleep(2)
        rr = run_test("ROUND ROBIN")
        input("\nTekan Enter untuk mulai Least Connections...")
        set_nginx_mode("least_conn")
        print("\nMode: LEAST CONNECTIONS")
        time.sleep(2)
        lc = run_test("LEAST CONNECTIONS")
        print_comparison(rr, lc)
        return

    if args.mode == "1":
        set_nginx_mode("round_robin")
        print("\nMode: ROUND ROBIN")
        run_test("ROUND ROBIN")
    elif args.mode == "2":
        set_nginx_mode("least_conn")
        print("\nMode: LEAST CONNECTIONS")
        run_test("LEAST CONNECTIONS")
    else:
        print("eCommerce SiCepat - Load Balancer Simulasi Flash Sale")
        print("Pilih mode:")
        print("  1. Round Robin")
        print("  2. Least Connections")
        print("  both = kedua algoritma berurutan")
        choice = input("Masukkan pilihan (1/2/both): ").strip()
        if choice == "1":
            set_nginx_mode("round_robin")
            print("\nMode: ROUND ROBIN")
            run_test("ROUND ROBIN")
        elif choice == "2":
            set_nginx_mode("least_conn")
            print("\nMode: LEAST CONNECTIONS")
            run_test("LEAST CONNECTIONS")
        elif choice == "both":
            input("\nTekan Enter untuk mulai Round Robin...")
            set_nginx_mode("round_robin")
            print("\nMode: ROUND ROBIN")
            time.sleep(2)
            rr = run_test("ROUND ROBIN")
            input("\nTekan Enter untuk mulai Least Connections...")
            set_nginx_mode("least_conn")
            print("\nMode: LEAST CONNECTIONS")
            time.sleep(2)
            lc = run_test("LEAST CONNECTIONS")
            print_comparison(rr, lc)

def print_comparison(rr, lc):
    print(f"\n{'=' * 50}")
    print("  HASIL PERBANDINGAN")
    print(f"{'=' * 50}")
    print(f"{'Metrik':30s} {'Round Robin':>15s} {'Least Conn':>15s}")
    print(f"{'-' * 30} {'-' * 15} {'-' * 15}")
    print(f"{'Total Waktu':30s} {rr['total_time']:>13.2f}s {lc['total_time']:>13.2f}s")
    print(f"{'Req ke Checkout':30s} {rr['distribution'].get('checkout', 0):>15d} {lc['distribution'].get('checkout', 0):>15d}")
    print(f"{'Req ke Katalog':30s} {rr['distribution'].get('katalog', 0):>15d} {lc['distribution'].get('katalog', 0):>15d}")
    print(f"{'Req ke Cart':30s} {rr['distribution'].get('cart', 0):>15d} {lc['distribution'].get('cart', 0):>15d}")
    print(f"\nKesimpulan:")
    speedup = rr['total_time'] / lc['total_time']
    print(f"  Least Connections {speedup:.0f}x lebih cepat dari Round Robin")
    print(f"  Round Robin membanjiri server checkout (lambat) dengan request")
    print(f"  Least Connections mengisolasi server checkout & maksimalkan server cepat")

if __name__ == "__main__":
    main()
