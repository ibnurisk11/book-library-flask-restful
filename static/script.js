// script.js
document.addEventListener('DOMContentLoaded', () => {
    const booksContainer = document.getElementById('books-container');
    const addBookForm = document.getElementById('add-book-form');
    const bookMessageElement = document.getElementById('book-message');
    
    // Elemen baru untuk peminjaman
    const borrowBookForm = document.getElementById('borrow-book-form');
    const borrowMemberSelect = document.getElementById('borrow_member_id');
    const borrowBookSelect = document.getElementById('borrow_book_id');
    const borrowingMessageElement = document.getElementById('borrowing-message');
    const borrowingsContainer = document.getElementById('borrowings-container');
    const returnBookForm = document.getElementById('return-book-form');
    const returnMessageElement = document.getElementById('return-message');

    // Elemen baru untuk anggota
    const addMemberForm = document.getElementById('add-member-form');
    const memberMessageElement = document.getElementById('member-message');
    const membersContainer = document.getElementById('members-container');

    // Elemen Navigasi Sidebar
    const sidebarLinks = document.querySelectorAll('.sidebar nav ul li a');
    const contentSections = document.querySelectorAll('.content-section');

    // Elemen Navigasi Sub-Section
    const borrowingSubNavButtons = document.querySelectorAll('#borrowing-management-section .section-nav button');
    const borrowingSubSections = document.querySelectorAll('.borrowing-sub-section');
    const memberSubNavButtons = document.querySelectorAll('#member-management-section .section-nav button');
    const memberSubSections = document.querySelectorAll('.member-sub-section');

    // **PERBAIKAN:** Mapping untuk ID sub-section peminjaman yang tidak mengikuti pola default
    const borrowingSubsectionIdMap = {
        'list': 'borrowings-list-subsection',
        'new': 'borrow-new-subsection', // ID di HTML adalah 'borrow-new-subsection'
        'return': 'return-book-subsection' // ID di HTML adalah 'return-book-subsection'
    };

    // **PERBAIKAN:** Mapping untuk ID sub-section anggota yang tidak mengikuti pola default
    const memberSubsectionIdMap = {
        'list': 'members-list-subsection',
        'new': 'add-member-subsection' // ID di HTML adalah 'add-member-subsection'
    };

    // Base URL dari API Flask Anda
    const API_BASE_URL = 'http://127.0.0.1:5000';

    // Fungsi untuk menampilkan pesan (diperbarui untuk menerima ID elemen pesan)
    function showMessage(msg, type, elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = msg;
            element.className = `message ${type}`;
            setTimeout(() => {
                element.textContent = '';
                element.className = 'message';
            }, 5000);
        }
    }

    // --- Fungsionalitas Navigasi Sidebar ---
    function showSection(sectionId) {
        contentSections.forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId + '-section').classList.add('active');

        // Update active link in sidebar
        sidebarLinks.forEach(link => {
            link.classList.remove('active-link');
            if (link.dataset.section === sectionId) {
                link.classList.add('active-link');
            }
        });
        // Refresh data saat pindah section
        if (sectionId === 'book-list') fetchBooks();
        if (sectionId === 'borrowing-management') {
            fetchBorrowings();
            fetchBooks(); // Untuk dropdown di form peminjaman
            fetchMembers(); // Untuk dropdown di form peminjaman
        }
        if (sectionId === 'member-management') fetchMembers();
    }

    // Event listener untuk link sidebar
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const sectionToShow = event.target.dataset.section;
            showSection(sectionToShow);
        });
    });

    // --- Fungsionalitas Navigasi Sub-Section ---
    function showSubSection(subSectionType, subSectionId) {
        const subSections = document.querySelectorAll(`.${subSectionType}-sub-section`);
        const navButtons = document.querySelectorAll(`#${subSectionType}-management-section .section-nav button`);

        subSections.forEach(section => {
            section.classList.remove('active');
        });

        // **PERBAIKAN:** Menggunakan mapping untuk mendapatkan ID elemen yang benar
        let targetId;
        if (subSectionType === 'borrowing') {
            targetId = borrowingSubsectionIdMap[subSectionId];
        } else if (subSectionType === 'member') {
            targetId = memberSubsectionIdMap[subSectionId];
        } else {
            // Fallback jika tipe tidak dikenal (seharusnya tidak terjadi jika data-attribute benar)
            targetId = `${subSectionType}s-${subSectionId}-subsection`;
        }
        
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.classList.add('active'); // Baris ini tidak akan lagi null jika ID cocok
        } else {
            console.error(`Elemen dengan ID "${targetId}" tidak ditemukan. Pastikan ID di HTML dan mapping di JS benar.`);
        }

        navButtons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset[`${subSectionType}SubSection`] === subSectionId) {
                button.classList.add('active');
            }
        });
        // Pastikan dropdown di-refresh saat beralih ke form peminjaman
        if (subSectionId === 'new' && subSectionType === 'borrowing') {
            fetchBooks();
            fetchMembers();
        }
    }

    // Event listener untuk tombol navigasi peminjaman
    borrowingSubNavButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const subSectionToShow = event.target.dataset.borrowingSubSection;
            showSubSection('borrowing', subSectionToShow);
        });
    });

    // Event listener untuk tombol navigasi anggota
    memberSubNavButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const subSectionToShow = event.target.dataset.memberSubSection;
            showSubSection('member', subSectionToShow);
        });
    });

    // Fungsi untuk mengambil dan menampilkan daftar buku
    async function fetchBooks() {
        booksContainer.innerHTML = '<p>Memuat buku...</p>';
        try {
            const response = await fetch(`${API_BASE_URL}/books`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const books = await response.json();
            
            if (books.length === 0) {
                booksContainer.innerHTML = '<p>Tidak ada buku yang ditemukan.</p>';
            } else {
                booksContainer.innerHTML = '';
                books.forEach(book => {
                    const bookCard = document.createElement('div');
                    bookCard.className = 'book-card';
                    bookCard.innerHTML = `
                        <h3>${book.judul}</h3>
                        <p><strong>Penulis ID:</strong> ${book.author_id}</p>
                        <p><strong>Kategori ID:</strong> ${book.category_id}</p>
                        <p><strong>Tahun Terbit:</strong> ${book.tahun_terbit || 'N/A'}</p>
                        <p><strong>ISBN:</strong> ${book.isbn || 'N/A'}</p>
                        <p class="stok"><strong>Stok:</strong> ${book.stok}</p>
                        <p><small>Ditambahkan: ${new Date(book.tanggal_dibuat).toLocaleDateString()}</small></p>
                    `;
                    booksContainer.appendChild(bookCard);
                });
            }
            populateBookSelect(books); 
        } catch (error) {
            console.error('Error fetching books:', error);
            booksContainer.innerHTML = `<p class="error-message">Gagal memuat buku: ${error.message}. Pastikan API Flask berjalan.</p>`; //
            showMessage('Gagal memuat buku.', 'error', 'book-message');
        }
    }

    // Fungsi untuk mengisi dropdown buku di formulir peminjaman
    function populateBookSelect(books) {
        borrowBookSelect.innerHTML = '<option value="">Pilih Buku</option>';
        books.forEach(book => {
            const option = document.createElement('option');
            option.value = book.id;
            option.textContent = `${book.judul} (Stok: ${book.stok})`;
            borrowBookSelect.appendChild(option);
        });
    }

    // Fungsi untuk mengambil dan menampilkan daftar anggota
    async function fetchMembers() {
        membersContainer.innerHTML = '<p>Memuat anggota...</p>';
        try {
            const response = await fetch(`${API_BASE_URL}/members`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const members = await response.json();

            if (members.length === 0) {
                membersContainer.innerHTML = '<p>Tidak ada anggota yang ditemukan.</p>';
            } else {
                membersContainer.innerHTML = '';
                members.forEach(member => {
                    const memberCard = document.createElement('div');
                    memberCard.className = 'book-card'; // Menggunakan style yang sama
                    memberCard.innerHTML = `
                        <h3>${member.nama} (ID: ${member.id})</h3>
                        <p><strong>Telepon:</strong> ${member.telepon}</p>
                        <p><strong>Email:</strong> ${member.email || 'N/A'}</p>
                        <p><strong>Alamat:</strong> ${member.alamat || 'N/A'}</p>
                        <p><small>Bergabung: ${new Date(member.tanggal_registrasi).toLocaleDateString()}</small></p>
                    `;
                    membersContainer.appendChild(memberCard);
                });
            }
            populateMemberSelect(members);
        }
        catch (error) {
            console.error('Error fetching members:', error);
            membersContainer.innerHTML = `<p class="error-message">Gagal memuat anggota: ${error.message}.</p>`;
            showMessage('Gagal memuat anggota.', 'error', 'member-message');
        }
    }

    // Fungsi untuk mengisi dropdown anggota di formulir peminjaman
    function populateMemberSelect(members) {
        borrowMemberSelect.innerHTML = '<option value="">Pilih Anggota</option>';
        members.forEach(member => {
            const option = document.createElement('option');
            option.value = member.id;
            option.textContent = `${member.nama} (ID: ${member.id})`;
            borrowMemberSelect.appendChild(option);
        });
    }

    // Fungsi untuk mengambil dan menampilkan daftar peminjaman
    async function fetchBorrowings() {
        borrowingsContainer.innerHTML = '<p>Memuat peminjaman...</p>';
        try {
            const response = await fetch(`${API_BASE_URL}/borrowings`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const borrowings = await response.json();

            if (borrowings.length === 0) {
                borrowingsContainer.innerHTML = '<p>Tidak ada riwayat peminjaman.</p>';
            } else {
                borrowingsContainer.innerHTML = '';
                borrowings.forEach(borrowing => {
                    const borrowingCard = document.createElement('div');
                    borrowingCard.className = 'book-card'; // Menggunakan style yang sama
                    const tglPeminjaman = new Date(borrowing.tanggal_peminjaman).toLocaleDateString();
                    const tglKembaliSeharusnya = new Date(borrowing.tanggal_kembali_seharusnya).toLocaleDateString();
                    const tglPengembalianAktual = borrowing.tanggal_pengembalian_aktual ? new Date(borrowing.tanggal_pengembalian_aktual).toLocaleDateString() : 'Belum Dikembalikan';
                    
                    let statusClass = '';
                    if (borrowing.status === 'dikembalikan') {
                        statusClass = 'status-dikembalikan';
                    } else if (borrowing.status === 'terlambat') {
                        statusClass = 'status-terlambat';
                    } else {
                        statusClass = 'status-dipinjam';
                    }

                    borrowingCard.innerHTML = `
                        <h3>Peminjaman ID: ${borrowing.id}</h3>
                        <p><strong>Buku:</strong> ${borrowing.book ? borrowing.book.judul : 'N/A'} (ID: ${borrowing.book_id})</p>
                        <p><strong>Anggota:</strong> ${borrowing.member ? borrowing.member.nama : 'N/A'} (ID: ${borrowing.member_id})</p>
                        <p><strong>Dipinjam:</strong> ${tglPeminjaman}</p>
                        <p><strong>Kembali Seharusnya:</strong> ${tglKembaliSeharusnya}</p>
                        <p><strong>Dikembalikan Aktual:</strong> ${tglPengembalianAktual}</p>
                        <p><strong>Status:</strong> <span class="${statusClass}">${borrowing.status.toUpperCase()}</span></p>
                    `;
                    borrowingsContainer.appendChild(borrowingCard);
                });
            }
        } catch (error) {
            console.error('Error fetching borrowings:', error);
            borrowingsContainer.innerHTML = `<p class="error-message">Gagal memuat peminjaman: ${error.message}.</p>`;
            showMessage('Gagal memuat peminjaman.', 'error', 'borrowing-message');
        }
    }

    // Event Listener untuk form Tambah Buku
    addBookForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const judul = document.getElementById('judul').value;
        const tahun_terbit = document.getElementById('tahun_terbit').value;
        const isbn = document.getElementById('isbn').value;
        const stok = document.getElementById('stok').value;
        const author_id = document.getElementById('author_id').value;
        const category_id = document.getElementById('category_id').value;

        const newBook = {
            judul: judul,
            tahun_terbit: tahun_terbit ? parseInt(tahun_terbit) : null,
            isbn: isbn || null,
            stok: parseInt(stok),
            author_id: parseInt(author_id),
            category_id: parseInt(category_id)
        };

        try {
            const response = await fetch(`${API_BASE_URL}/books`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newBook)
            });
            const result = await response.json();

            if (response.ok) {
                showMessage('Buku berhasil ditambahkan!', 'success', 'book-message');
                addBookForm.reset();
                fetchBooks(); // Muat ulang daftar buku dan dropdown
            } else {
                showMessage(`Gagal menambahkan buku: ${result.message || response.statusText}`, 'error', 'book-message');
            }
        } catch (error) {
            console.error('Error adding book:', error);
            showMessage(`Terjadi kesalahan saat menambahkan buku: ${error.message}`, 'error', 'book-message');
        }
    });

    // Event Listener untuk form Tambah Anggota
    addMemberForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const nama = document.getElementById('member_nama').value;
        const alamat = document.getElementById('member_alamat').value;
        const telepon = document.getElementById('member_telepon').value;
        const email = document.getElementById('member_email').value;

        const newMember = {
            nama: nama,
            alamat: alamat || null,
            telepon: telepon,
            email: email || null
        };

        try {
            const response = await fetch(`${API_BASE_URL}/members`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newMember)
            });
            const result = await response.json();

            if (response.ok) {
                showMessage('Anggota berhasil ditambahkan!', 'success', 'member-message');
                addMemberForm.reset();
                fetchMembers(); // Muat ulang daftar anggota dan dropdown
            } else {
                showMessage(`Gagal menambahkan anggota: ${result.message || response.statusText}`, 'error', 'member-message');
            }
        } catch (error) {
            console.error('Error adding member:', error);
            showMessage(`Terjadi kesalahan saat menambahkan anggota: ${error.message}`, 'error', 'member-message');
        }
    });

    // Event Listener untuk form Peminjaman Buku
    borrowBookForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const book_id = parseInt(borrowBookSelect.value);
        const member_id = parseInt(borrowMemberSelect.value);
        const durasi_peminjaman_hari = parseInt(document.getElementById('durasi_peminjaman_hari').value);

        if (!book_id || !member_id || isNaN(durasi_peminjaman_hari) || durasi_peminjaman_hari <= 0) {
            showMessage('Semua kolom peminjaman harus diisi dengan benar.', 'error', 'borrowing-message');
            return;
        }

        const newBorrowing = {
            book_id: book_id,
            member_id: member_id,
            durasi_peminjaman_hari: durasi_peminjaman_hari
        };

        try {
            const response = await fetch(`${API_BASE_URL}/borrowings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newBorrowing)
            });
            const result = await response.json();

            if (response.ok) {
                showMessage('Buku berhasil dipinjam!', 'success', 'borrowing-message');
                borrowBookForm.reset();
                fetchBooks(); // Update stok buku
                fetchBorrowings(); // Muat ulang daftar peminjaman
            } else {
                showMessage(`Gagal meminjam buku: ${result.message || response.statusText}`, 'error', 'borrowing-message');
            }
        } catch (error) {
            console.error('Error borrowing book:', error);
            showMessage(`Terjadi kesalahan saat meminjam buku: ${error.message}`, 'error', 'borrowing-message');
        }
    });

    // Event Listener untuk form Pengembalian Buku
    returnBookForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const borrowing_id = parseInt(document.getElementById('return_borrowing_id').value);

        if (isNaN(borrowing_id) || borrowing_id <= 0) {
            showMessage('ID Peminjaman harus diisi dengan angka yang valid.', 'error', 'return-message');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/borrowings/${borrowing_id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'dikembalikan' })
            });
            const result = await response.json();

            if (response.ok) {
                showMessage(`Peminjaman ID ${borrowing_id} berhasil dikembalikan!`, 'success', 'return-message');
                returnBookForm.reset();
                fetchBooks(); // Update stok buku
                fetchBorrowings(); // Muat ulang daftar peminjaman
            } else {
                showMessage(`Gagal mengembalikan buku: ${result.message || response.statusText}`, 'error', 'return-message');
            }
        } catch (error) {
            console.error('Error returning book:', error);
            showMessage(`Terjadi kesalahan saat mengembalikan buku: ${error.message}`, 'error', 'return-message');
        }
    });

    // Inisialisasi awal: tampilkan Daftar Buku sebagai halaman default
    showSection('book-list'); // Tampilkan section daftar buku
    fetchBooks(); // Ambil data buku
    // Fetch data lain hanya jika section mereka aktif atau dibutuhkan untuk dropdown
    fetchMembers(); // Untuk dropdown peminjaman
});