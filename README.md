# Sistem Penjadwalan Irigasi Berbasis CSP

Program ini merupakan implementasi **Constraint Satisfaction Problem
(CSP)** untuk menyusun jadwal irigasi secara otomatis berdasarkan:

-   Prioritas plot (**high → medium → low**)
-   Kebutuhan air tiap plot (`water_need_hours`)
-   Ketersediaan slot waktu pompa
-   Batas maksimum jam operasi pompa per hari

Algoritma CSP yang digunakan:

-   **Backtracking Search**
-   **Forward Checking (FC)**
-   **Arc Consistency (AC-3)**
-   **Heuristik:** Priority Ordering, Water Need Ordering, MRV,
    Degree
-   **Visualisasi Gantt Chart:** menunjukkan hasil jadwal

Program menghasilkan jadwal irigasi optimal tanpa konflik di slot yang sama dan
sesuai prioritas.

------------------------------------------------------------------------

## 1. Struktur Input

Program membaca dua file CSV:

### **a. plots.csv**

Berisi daftar plot, kebutuhan air, dan prioritas:

| plot_id | water_need_hours | priority |
| ------- | ---------------: | -------- |
| P1      |                2 | high     |
| P2      |                3 | medium   |
| ...     |              ... | ...      |


### **b. pump_settings.csv**

Berisi kapasitas pompa dan daftar slot waktu:

| max_hours_per_day | time_slots                  |
| ----------------: | --------------------------- |
|                20 | 06-07;07-08;08-09;...;22-23 |

> Format CSV harus valid agar parser bekerja dengan benar.

------------------------------------------------------------------------

## 2. Cara Menjalankan Program

### Persyaratan

-   Python **3.8+**

-   Library:

    ``` bash
    pip install pandas matplotlib
    ```

### Menjalankan Program

Pastikan file berikut berada dalam satu folder:

-   `irrigation.py`
-   `plots.csv`
-   `pump_settings.csv`

Jalankan melalui terminal:

``` bash
python irrigation.py
```

### Output yang dihasilkan

-   Jadwal irigasi lengkap
-   Total waktu pompa
-   Runtime komputasi
-   Visualisasi **Gantt Chart** jadwal irigasi

------------------------------------------------------------------------

## 3. Fitur Utama

-   **AC-3** untuk meminimalkan domain dan memastikan _arc consistency_
-   **Forward Checking** untuk memotong domain sebelum pendalaman
    pencarian
-   **Backtracking Search** untuk menemukan solusi jadwal
-   **Heuristik CSP:**
    -   Priority Ordering (high → medium → low)
    -   Water Need Ordering (kebutuhan air lebih besar diprioritaskan)
    -   MRV (Minimum Remaining Values)
    -   Degree heuristic
-   Pembuatan domain otomatis berdasarkan _water needs_
-   Gantt Chart berwarna sesuai prioritas

------------------------------------------------------------------------

## 4. Contoh Output

    JADWAL IRIGASI DITEMUKAN
    Plot P4 (high) -> 06-07 & 07-08 & 08-09 & 09-10
    Plot P1 (high) -> 10-11 & 11-12
    Plot P5 (high) -> 12-13 & 13-14
    Plot P2 (medium) -> 14-15 & 15-16 & 16-17
    Plot P6 (low) -> 17-18 & 18-19 & 19-20
    Plot P3 (low) -> 20-21
    Plot P7 (low) -> 21-22

    Total Waktu Pompa: 16 Jam / 20 Jam
    Waktu Komputasi: 6.1830 detik

**Gantt Chart** akan terbuka secara otomatis.

------------------------------------------------------------------------

## 5. Notes

-   Program dapat menangani format CSV yang kurang rapi
-   Jika AC-3 menghasilkan domain kosong → output solusi **tidak mungkin**
-   Jika runtime lama, kurangi jumlah slot atau plot
