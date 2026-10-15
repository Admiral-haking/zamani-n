// ========================================
// ZAMANI DASHBOARD - نسخه نهایی کامل با Notifications
// ========================================

class Dashboard {
    constructor() {
        this.userData = null;
        this.customerData = null;
        this.recentOrders = [];
        this.cartData = null;
        this.returnRequests = [];
        this.cheques = [];
        this.tickets = [];
        this.notifications = [];
        this.mySummary = null;
        this.transactions = [];
        this.isLoading = true;
        this.init();
    }

    async init() {
        console.log('📊 راه‌اندازی داشبورد...');

        const token = getAccessToken();
        if (!token) {
            console.warn('⛔ توکن یافت نشد، هدایت به صفحه لاگین');
            window.location.href = 'log.html';
            return;
        }

        try {
            await this.loadAllData();
            this.renderDashboard();
            this.jalaliEnhanceCust();
            this.showToast('✅ داشبورد با موفقیت بارگذاری شد', 'success');
        } catch (error) {
            console.error('❌ خطا در بارگذاری داشبورد:', error);
            this.showToast('❌ خطا در بارگذاری اطلاعات داشبورد', 'error');
        } finally {
            this.isLoading = false;
            this.hideLoader();
        }
    }

    async loadAllData() {
        const results = await Promise.allSettled([
            this.loadUserData(),
            this.loadCustomerData(),
            this.loadRecentOrders(),
            this.loadCartData(),
            this.loadReturnRequests(),
            this.loadCheques(),
            this.loadTickets(),
            this.loadNotifications(),
            this.loadMySummary(),
            this.loadTransactions()
        ]);

        const labels = ['User', 'Customer', 'Orders', 'Cart', 'Returns', 'Cheques', 'Tickets', 'Notifications', 'MySummary', 'Transactions'];
        results.forEach((result, index) => {
            if (result.status === 'fulfilled') {
                console.log(`✅ ${labels[index]} loaded successfully`);
            } else {
                console.warn(`⚠️ ${labels[index]} failed:`, result.reason);
            }
        });

        return results;
    }

    async loadUserData() {
        const response = await apiGet('accounts/me/');
        if (response.success) {
            this.userData = response.data;
            console.log('👤 User Data:', this.userData);
            return this.userData;
        } else {
            throw new Error(response.data?.detail || 'خطا در دریافت اطلاعات کاربر');
        }
    }

    async loadCustomerData() {
        const response = await apiGet('customers/');
        if (response.success) {
            this.customerData = response.data.results?.[0] || response.data;
            console.log('🏢 Customer Data:', this.customerData);
            return this.customerData;
        } else {
            console.warn('⚠️ اطلاعات مشتری یافت نشد');
            this.customerData = null;
            return null;
        }
    }

    async loadRecentOrders() {
        const response = await apiGet('orders/');
        if (response.success) {
            this.recentOrders = response.data.results || response.data || [];
            console.log('📦 Recent Orders:', this.recentOrders);
            return this.recentOrders;
        } else {
            console.warn('⚠️ خطا در دریافت سفارشات');
            this.recentOrders = [];
            return [];
        }
    }

    async loadCartData() {
        const response = await apiGet('cart/');
        if (response.success) {
            this.cartData = response.data;
            console.log('🛒 Cart Data (API):', this.cartData);
            return this.cartData;
        } else {
            console.warn('⚠️ خطا در دریافت سبد خرید از API');
            this.cartData = null;
            return null;
        }
    }

    async loadReturnRequests() {
        const response = await apiGet('returns/');
        if (response.success) {
            this.returnRequests = response.data.results || response.data || [];
            console.log('📦 Return Requests:', this.returnRequests);
            return this.returnRequests;
        } else {
            console.warn('⚠️ خطا در دریافت درخواست‌های مرجوعی');
            this.returnRequests = [];
            return [];
        }
    }

    // ========================================
    // بارگذاری چک‌ها - از API واقعی
    // ========================================
    async loadCheques() {
        const response = await apiGet('finance/checks/');
        if (response.success) {
            this.cheques = response.data.results || response.data || [];
            console.log('📄 Cheques (API):', this.cheques);
            return this.cheques;
        } else {
            console.warn('⚠️ خطا در دریافت چک‌ها');
            this.cheques = [];
            return [];
        }
    }

    // ========================================
    // ثبت چک جدید - به API واقعی
    // ========================================
    async submitCheque(data) {
        try {
            const response = await apiPost('finance/checks/', data);
            
            if (response.success) {
                this.showToast('✅ چک با موفقیت ثبت شد', 'success');
                await this.loadCheques();
                this.renderCheques();
                document.getElementById('chequeModalOverlay').classList.remove('active');
                return true;
            } else {
                this.showToast('❌ خطا در ثبت چک: ' + (response.data?.detail || 'خطا'), 'error');
                return false;
            }
        } catch (error) {
            console.error('❌ Error submitting cheque:', error);
            this.showToast('❌ خطا در ارتباط با سرور', 'error');
            return false;
        }
    }

    // ========================================
    // گزارش مالی شخصی (my_summary)
    // ========================================
    async loadMySummary() {
        const response = await apiGet('finance/transactions/my_summary/');
        if (response.success) {
            this.mySummary = response.data;
            console.log('📊 My Summary:', this.mySummary);
            return this.mySummary;
        } else {
            console.warn('⚠️ خطا در دریافت گزارش مالی شخصی');
            this.mySummary = null;
            return null;
        }
    }

    // ========================================
    // تراکنش‌های مالی (تاریخچه شارژ/پرداخت)
    // ========================================
    async loadTransactions() {
        const response = await apiGet('finance/transactions/');
        if (response.success) {
            this.transactions = response.data.results || response.data || [];
            console.log('💳 Transactions:', this.transactions);
            return this.transactions;
        } else {
            console.warn('⚠️ خطا در دریافت تراکنش‌ها');
            this.transactions = [];
            return [];
        }
    }

    // ========================================
    // رندر تراکنش‌ها (تاریخچه پرداخت)
    // ========================================
    renderWalletHistory(filterType = 'this_month', fromDate = null, toDate = null) {
        const body = document.getElementById('walletHistoryBody');
        if (!body) return;

        const transactions = this.transactions || [];
        if (transactions.length === 0) {
            body.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-gray);">
                <i class="fas fa-wallet" style="font-size:24px;display:block;margin-bottom:8px;color:var(--mustard-yellow);"></i>
                تراکنشی یافت نشد.</td></tr>`;
            return;
        }

        let filtered = [...transactions];
        if (filterType && filterType !== 'all') {
            const now = new Date();
            filtered = filtered.filter(tx => {
                if (!tx.created_at) return false;
                const d = new Date(tx.created_at);
                if (filterType === 'today') return d.toDateString() === now.toDateString();
                if (filterType === 'yesterday') {
                    const yesterdayStart = new Date(now);
                    yesterdayStart.setDate(now.getDate() - 1);
                    yesterdayStart.setHours(0, 0, 0, 0);
                    const todayStart = new Date(now);
                    todayStart.setHours(0, 0, 0, 0);
                    return d >= yesterdayStart && d < todayStart;
                }
                if (filterType === 'this_week') {
                    const diff = (now.getDay() === 0) ? 6 : now.getDay() - 1;
                    const weekStart = new Date(now);
                    weekStart.setDate(weekStart.getDate() - diff);
                    return d >= weekStart;
                }
                if (filterType === 'this_month') {
                    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
                    return d >= monthStart;
                }
                if (filterType === 'this_year') {
                    const yearStart = new Date(now.getFullYear(), 0, 1);
                    return d >= yearStart;
                }
                if (filterType === 'custom' && fromDate) {
                    const start = new Date(`${fromDate}T00:00:00`);
                    const end = toDate ? new Date(`${toDate}T23:59:59`) : new Date();
                    return d >= start && d <= end;
                }
                return true;
            });
        }

        if (filtered.length === 0) {
            body.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-gray);">
                تراکنشی در این بازه زمانی یافت نشد.</td></tr>`;
            return;
        }

        const escTx = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
        let html = '';
        let totalAmount = 0;
        filtered.slice(0, 30).forEach((tx, index) => {
            const isCredit = ['PAYMENT', 'RETURN'].includes(tx.transaction_type);
            const amount = tx.amount || 0;
            if (isCredit) totalAmount += Number(amount);
            const prods = Array.isArray(tx.order_products) ? tx.order_products : [];
            const desc = prods.length
                ? prods.map(p => escTx(p.name || 'محصول') + (p.quantity ? ` <span style="color:var(--text-gray);font-size:11px;">${Number(p.quantity).toLocaleString('fa-IR')} عدد</span>` : '')).join('<br>')
                : escTx(tx.description || tx.transaction_type || '—');
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td><span dir="ltr" style="color:var(--mustard-yellow);">${escTx(tx.order_invoice || '—')}</span></td>
                    <td>${this.formatDate(tx.created_at)}</td>
                    <td style="min-width:170px;">${desc}</td>
                    <td>${this.formatPrice(amount)}</td>
                    <td><span class="tx-status ${isCredit ? 'success' : 'pending'}">${tx.status_label || tx.status || '—'}</span></td>
                    <td>${isCredit ? 'تسویه شده' : 'مانده حساب'}</td>
                    <td>${tx.payment_receipt ? `<a href="${tx.payment_receipt}" target="_blank" rel="noopener" class="btn-secondary btn-sm" style="text-decoration:none;"><i class="fas fa-paperclip"></i> رسید</a>` : '—'}</td>
                </tr>
            `;
        });
        body.innerHTML = html;
    }

    // ========================================
    // رندر گزارش مالی (خلاصه + جدول سفارشات)
    // ========================================
    renderFinancial() {
        const tableBody = document.getElementById('financialTableBody');
        if (!tableBody) return;

        const orders = this.recentOrders || [];
        const summary = this.mySummary || {};

        // کارت‌های خلاصه
        const balanceEl = document.getElementById('financialBalance');
        const purchaseEl = document.getElementById('financialTotalPurchase');
        const dailyEl = document.getElementById('financialDaily');
        const weeklyEl = document.getElementById('financialWeekly');
        if (balanceEl) balanceEl.textContent = this.formatPrice(summary.balance !== undefined ? summary.balance : 0);
        if (purchaseEl) purchaseEl.textContent = this.formatPrice(summary.total_purchase || 0);
        if (dailyEl) dailyEl.textContent = this.formatPrice(summary.today?.expense || 0);
        if (weeklyEl) weeklyEl.textContent = this.formatPrice(summary.week?.expense || 0);
        const walletEl = document.getElementById('walletBalance');
        if (walletEl) walletEl.textContent = this.formatPrice(summary.balance !== undefined ? summary.balance : 0);

        if (orders.length === 0) {
            tableBody.innerHTML = `
                <tr class="section-header"><td colspan="11"><i class="fas fa-shopping-bag"></i> سفارشات</td></tr>
                <tr><td colspan="11" style="text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-inbox" style="font-size:24px;display:block;margin-bottom:10px;color:var(--mustard-yellow);"></i>
                    هنوز سفارشی برای شما ثبت نشده است.</td></tr>`;
            return;
        }

        let html = `
            <tr class="section-header"><td colspan="11"><i class="fas fa-shopping-bag"></i> سفارشات</td></tr>
        `;
        let totalAll = 0, totalPaid = 0, totalRemain = 0;

        orders.forEach((order, index) => {
            const paid = order.paid_amount || 0;
            const total = (order.total_price || order.total_amount || 0);
            const remain = this.orderOutstanding(order);
            totalAll += total;
            totalPaid += paid;
            totalRemain += remain;

            let productNames = [];
            if (order.items && order.items.length > 0) {
                productNames = order.items.map(item => item.product?.name || item.product_name || item.name || 'محصول');
            }
            const description = productNames[0] || '—';

            const paymentLabels = {
                'ONLINE': 'آنلاین', 'CARD': 'کارت به کارت', 'CASH': 'نقدی', 'CHEQUE': 'چکی', 'CHECK': 'پرداخت چکی', 'BALANCE': 'مانده حساب', 'CREDIT': 'اعتباری'
            };

            const receipts = (Array.isArray(order.payments) ? order.payments : []).filter(p => p && p.receipt);

            html += `
                <tr data-date="${this.formatDate(order.created_at)}" data-invoice="#${order.id}">
                    <td>${index + 1}</td>
                    <td>#${order.id}</td>
                    <td>${this.formatDate(order.created_at)}</td>
                    <td>${description}</td>
                    <td>${this.formatPrice(total)}</td>
                    <td><span class="status-badge ${remain === 0 ? 'paid' : 'partial'}">${this.formatPrice(paid)}</span></td>
                    <td><span class="remain-amount ${remain === 0 ? 'zero' : 'positive'}">${this.formatPrice(remain)}</span></td>
                    <td><span class="payment-method ${(order.payment_method || 'cash').toLowerCase()}"><i class="fas fa-money-bill-wave"></i> ${paymentLabels[order.payment_method] || this.getPaymentMethodLabel(order.payment_method)}</span></td>
                    <td><span class="profit-badge">—</span></td>
                    <td><span class="status-badge ${order.status}">${this.getStatusLabel(order.status)}</span></td>
                    <td>
                        ${receipts.length ? `<a class="btn-secondary btn-sm" href="${receipts[0].receipt}" target="_blank" rel="noopener" title="مشاهده رسید پرداخت" style="padding:3px 10px;margin-left:4px;text-decoration:none;"><i class="fas fa-paperclip"></i> رسید</a>` : ''}
                        <button class="btn-secondary btn-sm print-order-btn" data-order-id="${order.id}" title="چاپ فاکتور این سفارش" style="padding:3px 10px;">
                            <i class="fas fa-print"></i> چاپ فاکتور
                        </button>
                    </td>
                </tr>
            `;
        });

        html += `
            <tr class="total-row">
                <td colspan="4" style="text-align:center;"><i class="fas fa-calculator"></i> جمع کل</td>
                <td>${this.formatPrice(totalAll)}</td>
                <td>${this.formatPrice(totalPaid)}</td>
                <td>${this.formatPrice(totalRemain)}</td>
                <td colspan="4">—</td>
            </tr>
        `;
        tableBody.innerHTML = html;

        tableBody.querySelectorAll('.print-order-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = parseInt(btn.dataset.orderId);
                const order = orders.find(o => o.id === id);
                if (order) this.printInvoice(order);
            });
        });
    }

    // ========================================
    // چاپ فاکتور (سبک حسابداری)
    // ========================================
    printInvoice(order) {
        if (!order) return;

        const fa = (n) => {
            if (n === null || n === undefined || isNaN(Number(n))) return '۰';
            return Math.round(Number(n)).toLocaleString('fa-IR');
        };
        const money = (n) => fa(n) + ' تومان';
        const fmt = (d) => this.formatDate(d);

        const user = this.userData || {};
        const items = Array.isArray(order.items) ? order.items : [];
        const paid = order.paid_amount || 0;
        const total = order.total_price || order.total_amount || 0;
        const remain = this.orderOutstanding(order);

        const paymentLabels = {
            'ONLINE': 'آنلاین', 'CARD': 'کارت به کارت', 'CASH': 'نقدی', 'CHEQUE': 'چکی', 'CHECK': 'پرداخت چکی', 'BALANCE': 'مانده حساب', 'CREDIT': 'اعتباری'
        };

        const itemRows = items.map((it, i) => {
            const name = it.product?.name || it.product_name || it.name || 'محصول';
            const qty = parseInt(it.quantity) || 1;
            const price = it.price || 0;
            return `<tr>
                <td style="text-align:center;">${fa(i + 1)}</td>
                <td>${name}</td>
                <td style="text-align:center;">${fa(qty)}</td>
                <td>${money(price)}</td>
                <td>${money(it.discount || 0)}</td>
                <td>${money(price * qty)}</td>
            </tr>`;
        }).join('') || `<tr><td colspan="6" style="text-align:center;color:#999;">—</td></tr>`;

        const html = `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>فاکتور فروش</title>
<style>
    @page { size: A4; margin: 12mm; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Tahoma, "Segoe UI", Arial, sans-serif; color: #1a1a1a; background: #fff; padding: 20px; }
    .invoice { max-width: 820px; margin: 0 auto; border: 3px solid #1f3864; background: #fff; }
    .invoice-header { text-align: center; padding: 24px 22px 16px; background: #f7f9fc; border-bottom: 3px solid #f5c518; }
    .invoice-header .logo { height: 86px; max-width: 240px; object-fit: contain; }
    .brand-name { font-size: 26px; font-weight: bold; color: #1f3864; letter-spacing: 3px; margin-top: 6px; }
    .head-strip { display: flex; justify-content: space-between; align-items: center; gap: 12px; background: #1f3864; color: #fff; padding: 12px 22px; font-size: 13px; flex-wrap: wrap; }
    .head-strip .side { font-size: 12.5px; line-height: 1.9; }
    .head-strip .doc-title { background: #f5c518; color: #111; font-weight: bold; font-size: 15px; padding: 6px 24px; border-radius: 4px; }
    .meta { display: flex; flex-wrap: wrap; gap: 10px 28px; padding: 14px 24px; font-size: 13px; border-bottom: 2px solid #e6e8ee; }
    .meta div { line-height: 2; }
    .meta b { display: inline-block; min-width: 74px; color: #1f3864; }
    table { width: 100%; border-collapse: collapse; }
    .items th { background: #1f3864; color: #fff; padding: 11px 10px; font-size: 13px; border: 2px solid #1f3864; }
    .items td { padding: 10px; font-size: 13px; border: 2px solid #33415e; }
    .items tbody tr:nth-child(even) td { background: #f5f7fb; }
    .totals { width: 46%; margin-right: auto; margin-top: 16px; border: 2px solid #33415e; }
    .totals td { padding: 10px 14px; font-size: 13.5px; border: 2px solid #33415e; }
    .totals .final { background: #fff3cd; font-weight: bold; font-size: 14.5px; }
    .sign { display: flex; justify-content: space-between; gap: 28px; margin-top: 40px; padding: 0 30px; font-size: 12.5px; color: #444; }
    .sign .box { text-align: center; width: 42%; border-top: 2px solid #444; padding-top: 10px; font-weight: bold; }
    .terms { margin: 24px 24px 0; padding: 14px 16px; border: 2px dashed #1f3864; background: #f8fafd; font-size: 12.5px; line-height: 2.1; }
    .terms .card { font-weight: bold; color: #1f3864; font-size: 13.5px; }
    .terms .text { color: #333; text-align: justify; margin-top: 4px; }
    .footer { text-align: center; font-size: 11.5px; color: #777; padding: 16px; border-top: 2px solid #e6e8ee; margin-top: 22px; }
    .btn-print { display: block; margin: 18px auto; padding: 10px 26px; font-size: 14px; cursor: pointer; background: #1f3864; color: #fff; border: none; border-radius: 6px; }
    @media print { .btn-print { display: none; } }
</style>
</head>
<body>
    <button class="btn-print" onclick="window.print()">🖨 چاپ فاکتور</button>
    <div class="invoice">
        <div class="invoice-header">
            <img src="image/sarfactor.jpg" alt="سر فاکتور" class="logo"
                 onerror="this.onerror=null;var d=this.dataset;if(!d.f){d.f=1;this.src='image/logo.jpg';}if(!d.s){d.s=1;this.src='image/log/logo.jpg';}">
            <div class="brand-name">پخش زمانی</div>
        </div>
        <div class="head-strip">
            <div class="side" style="text-align:right;">شماره فاکتور: #${fa(order.id)}</div>
            <div class="doc-title">فاکتور فروش</div>
            <div class="side" style="text-align:left;">تاریخ: ${fmt(order.created_at)}</div>
        </div>
        <div class="meta">
            <div><b>نام مشتری:</b> ${order.customer_name || user.full_name || user.username || '—'}</div>
            <div><b>تلفن:</b> ${user.phone || '—'}</div>
            <div><b>کد رهگیری:</b> ${order.tracking_code || '—'}</div>
            <div><b>روش پرداخت:</b> ${paymentLabels[order.payment_method] || order.payment_method || '—'}</div>
            <div><b>وضعیت:</b> ${this.getStatusLabel(order.status)}</div>
        </div>
        <table class="items">
            <thead>
                <tr>
                    <th style="width:6%;">ردیف</th>
                    <th>شرح کالا</th>
                    <th style="width:10%;">تعداد</th>
                    <th style="width:18%;">قیمت واحد</th>
                    <th style="width:18%;">مبلغ تخفیف</th>
                    <th style="width:18%;">مبلغ کل</th>
                </tr>
            </thead>
            <tbody>${itemRows}</tbody>
        </table>
        <table class="totals">
            <tr><td>مبلغ کل</td><td style="text-align:left;">${money(total)}</td></tr>
            <tr><td>تخفیف کل</td><td style="text-align:left;">${money(order.total_discount || 0)}</td></tr>
            <tr><td>پرداخت شده</td><td style="text-align:left;">${money(paid)}</td></tr>
            <tr class="final"><td>مانده حساب</td><td style="text-align:left;">${money(remain)}</td></tr>
        </table>
        <div class="sign">
            <div class="box">امضا و مهر فروشنده</div>
            <div class="box">امضای خریدار</div>
        </div>
        <div class="terms">
            <div class="card">ش کارت : <span dir="ltr">5041721056972384</span> محسن زمانی راد(بانک رسالت)</div>
            <div class="text">این فاکتور پس از امضاء اینجانب یا نماینده ام سند تجاری تلقی شده و اجناس این فاکتور را صحیح و سالم تحویل گرفته و متعهد به پرداخت کل مانده حساب می باشم</div>
        </div>
        <div class="footer">با تشکر از خرید شما — پخش زمانی</div>
    </div>
</body>
</html>`;

        const win = window.open('', '_blank', 'width=820,height=950');
        if (!win) {
            showAlert('⚠️ لطفا اجازه باز شدن پنجره جدید را بدهید', 'error');
            return;
        }
        win.document.write(html);
        win.document.close();
        win.focus();
    }

    renderDashboard() {
        this.renderUserInfo();
        this.renderCustomerInfo();
        this.renderRecentOrders();
        this.renderCartStatus();
        this.renderAddresses();
        this.renderWishlist();
        this.renderRecommended();
        this.renderCoupons();
        this.renderTracking();
        this.renderReturns();
        this.renderCheques();
        this.renderTickets();
        this.renderFinancial();
        this.renderNotifications();
        this.renderWalletHistory('this_month');
        this.updateHeader();
    }

    // ========================================
    // رندر اطلاعات کاربری
    // ========================================
    renderUserInfo() {
        if (!this.userData) {
            console.warn('⚠️ No user data to render');
            return;
        }

        const user = this.userData;
        console.log('🔄 Rendering user info:', user);

        const allGrids = document.querySelectorAll('#section-profile .info-grid');
        console.log('📦 Found info-grids:', allGrids.length);

        if (allGrids.length >= 1) {
            const container = allGrids[0];
            container.innerHTML = `
                <div class="info-card">
                    <div class="label">نام کاربری</div>
                    <div class="value">${user.username || '---'}</div>
                </div>
                <div class="info-card">
                    <div class="label">نقش</div>
                    <div class="value gold">${this.getRoleLabel(user.role)}</div>
                </div>
                <div class="info-card">
                    <div class="label">ایمیل</div>
                    <div class="value">${user.email || 'ثبت نشده'}</div>
                </div>
                <div class="info-card">
                    <div class="label">شماره تماس</div>
                    <div class="value">${user.phone || 'ثبت نشده'}</div>
                </div>
            `;
            console.log('✅ User info grid updated!');
        }

        if (allGrids.length >= 2 && this.customerData) {
            const c = this.customerData;
            const container = allGrids[1];
            container.innerHTML = `
                <div class="info-card" style="grid-column: span 2;">
                    <div class="label">آدرس کامل</div>
                    <div class="value">${c.address || '---'}</div>
                </div>
                <div class="info-card">
                    <div class="label">کد پستی</div>
                    <div class="value">${c.postal_code || '---'}</div>
                </div>
                <div class="info-card">
                    <div class="label">استان / شهر</div>
                    <div class="value">${c.state || '---'} / ${c.city || '---'}</div>
                </div>
            `;
            console.log('✅ Address grid updated!');
        }

        const welcomeEl = document.querySelector('.panel-welcome h2');
        if (welcomeEl) {
            welcomeEl.textContent = `سلام، ${this.userData.username} 👋`;
        }

        const avatarEl = document.querySelector('.panel-avatar');
        if (avatarEl) {
            avatarEl.textContent = this.userData.username?.charAt(0)?.toUpperCase() || 'م';
        }

        this.renderCustomerInfo();
    }

    // ========================================
    // رندر اطلاعات مشتری
    // ========================================
    renderCustomerInfo() {
        if (!this.customerData) return;

        const c = this.customerData;
        console.log('🔄 Rendering customer info:', c);

        const walletSection = document.querySelector('#section-wallet .wallet-balance .balance-number');
        if (walletSection) {
            walletSection.textContent = (c.account_balance || 0).toLocaleString('fa-IR');
        }

        const balanceBadge = document.querySelector('.panel-badge:first-child');
        if (balanceBadge) {
            balanceBadge.innerHTML = `<i class="fas fa-wallet"></i> مانده حساب: ${this.formatPrice(c.account_balance)}`;
        }

        const addressBadge = document.querySelector('.panel-badge:last-child');
        if (addressBadge && c.address) {
            const shortAddr = c.address.length > 20 ? c.address.substring(0, 20) + '...' : c.address;
            addressBadge.innerHTML = `<i class="fas fa-map-pin"></i> ${shortAddr}`;
        }
    }

    // ========================================
    // رندر آدرس‌ها
    // ========================================
    renderAddresses() {
        const container = document.getElementById('addressList');
        if (!container) return;

        if (this.customerData && this.customerData.address) {
            const c = this.customerData;
            const addresses = [{
                id: c.id,
                title: 'آدرس ثبت‌شده',
                full: c.address || 'آدرسی ثبت نشده',
                province: c.state || '…',
                city: c.city || '…',
                postal: c.postal_code || '…',
                phone: c.phone || '—',
                isDefault: true
            }];

            container.innerHTML = addresses.map(addr => `
                <div class="address-card" data-id="${addr.id}">
                    <div class="address-title">
                        <i class="fas fa-home"></i>
                        ${addr.title}
                        ${addr.isDefault ? '<span class="badge-default">پیش‌فرض</span>' : ''}
                    </div>
                    <div class="address-detail">
                        ${addr.full}<br>
                        ${addr.city}، ${addr.province} - کد پستی: ${addr.postal}<br>
                        تلفن: ${addr.phone}
                    </div>
                    <div class="address-actions">
                        <button class="btn-edit-address" data-id="${addr.id}">
                            <i class="fas fa-edit"></i> ویرایش
                        </button>
                    </div>
                </div>
            `).join('');

            container.querySelectorAll('.btn-edit-address').forEach(btn => {
                btn.addEventListener('click', function() {
                    const id = parseInt(this.dataset.id);
                    document.getElementById('addressTitle').value = 'آدرس ثبت‌شده';
                    document.getElementById('addressFull').value = c.address || '';
                    document.getElementById('addressProvince').value = c.state || '';
                    document.getElementById('addressCity').value = c.city || '';
                    document.getElementById('addressPostal').value = c.postal_code || '';
                    document.getElementById('addressPhone').value = c.phone || '';
                    document.getElementById('addressModalOverlay').classList.add('active');
                    document.body.style.overflow = 'hidden';
                });
            });

        } else {
            container.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-map-pin" style="font-size:40px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ آدرسی ثبت نشده است.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای ثبت آدرس، روی دکمه "آدرس جدید" کلیک کنید.
                    </p>
                </div>
            `;
        }
    }

    // ========================================
    // رندر علاقه‌مندی‌ها
    // ========================================
    renderWishlist() {
        const container = document.getElementById('wishlistGrid');
        if (!container) return;

        let wishlistItems = JSON.parse(localStorage.getItem('zamaniWishlist')) || [];

        if (wishlistItems && wishlistItems.length > 0) {
            let html = '';
            wishlistItems.forEach((item, index) => {
                html += `
                    <div class="wishlist-item-card">
                        <div class="wishlist-img" style="background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 48px; color: var(--mustard-yellow);">
                            <img src="${item.image}" alt="${item.name}" style="width:100%;height:100%;object-fit:cover;border-radius:14px 14px 0 0;">
                        </div>
                        <div class="wishlist-info">
                            <div class="wishlist-name">${item.name}</div>
                            <div class="wishlist-price">${item.price} تومان</div>
                            <div class="wishlist-actions">
                                <button class="btn-add-cart-wishlist" data-index="${index}">
                                    <i class="fas fa-shopping-cart"></i> افزودن به سبد خرید
                                </button>
                                <button class="btn-remove-wishlist" data-index="${index}">
                                    <i class="fas fa-trash"></i> حذف
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            container.querySelectorAll('.btn-add-cart-wishlist').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    let wishlist = JSON.parse(localStorage.getItem('zamaniWishlist')) || [];
                    const item = wishlist[index];
                    if (item) {
                        let cart = JSON.parse(localStorage.getItem('zamaniCart')) || [];
                        const existing = cart.find(c => c.id === item.id);
                        if (existing) {
                            existing.quantity = (existing.quantity || 1) + 1;
                        } else {
                            cart.push({
                                id: item.id,
                                name: item.name,
                                price: parseInt(item.price.replace(/,/g, '')),
                                image: item.image,
                                quantity: 1,
                                type: 'package'
                            });
                        }
                        localStorage.setItem('zamaniCart', JSON.stringify(cart));
                        
                        if (window.dashboard) {
                            window.dashboard.renderCartStatus();
                        }
                        
                        window.dashboard.showToast(`🛒 ${item.name} به سبد خرید اضافه شد`, 'success');
                    }
                });
            });

            container.querySelectorAll('.btn-remove-wishlist').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    if (confirm('آیا از حذف این محصول از علاقه‌مندی‌ها مطمئن هستید؟')) {
                        let wishlist = JSON.parse(localStorage.getItem('zamaniWishlist')) || [];
                        wishlist.splice(index, 1);
                        localStorage.setItem('zamaniWishlist', JSON.stringify(wishlist));
                        
                        if (window.dashboard) {
                            window.dashboard.renderWishlist();
                        }
                        
                        const badge = document.getElementById('wishlistBadge');
                        if (badge) badge.textContent = wishlist.length;
                        
                        window.dashboard.showToast('🗑️ محصول از علاقه‌مندی‌ها حذف شد', 'info');
                    }
                });
            });

        } else {
            container.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-heart" style="font-size:48px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هنوز محصولی به علاقه‌مندی‌ها اضافه نکرده‌اید.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای افزودن محصول به علاقه‌مندی‌ها، به صفحه <a href="index.html" style="color:var(--mustard-yellow);">خانه</a> بروید و روی قلب ❤️ کلیک کنید.
                    </p>
                </div>
            `;
        }

        const badge = document.getElementById('wishlistBadge');
        if (badge) {
            const items = JSON.parse(localStorage.getItem('zamaniWishlist')) || [];
            badge.textContent = items.length;
        }
    }

    // ========================================
    // رندر پیشنهادات
    // ========================================
    renderRecommended() {
        const container = document.getElementById('recommendedGrid');
        if (!container) return;

        const recommendedProducts = [
            { id: 101, name: 'همبرگر ۱۲۵ گرمی ۹۰٪', price: '۱۸۹,۰۰۰', image: '🍔', badge: 'پرفروش' },
            { id: 102, name: 'استیک ۶۰٪', price: '۱۸۹,۰۰۰', image: '🥩', badge: 'پیشنهاد ویژه' },
            { id: 103, name: 'همبرگر ۱۰۰ گرمی ۶۰٪', price: '۹۹,۰۰۰', image: '🍔', badge: 'اقتصادی' },
            { id: 104, name: 'رست بیف ۹۰٪', price: '۲۹۹,۰۰۰', image: '🥩', badge: 'کیفیت عالی' }
        ];

        const wishlist = JSON.parse(localStorage.getItem('zamaniWishlist')) || [];
        const cart = JSON.parse(localStorage.getItem('zamaniCart')) || [];
        const existingIds = new Set([...wishlist.map(i => i.id), ...cart.map(i => i.id)]);
        
        const filteredRecommendations = recommendedProducts.filter(p => !existingIds.has(p.id));

        if (filteredRecommendations.length > 0) {
            let html = '';
            filteredRecommendations.forEach(product => {
                html += `
                    <div class="recommended-card" data-product-id="${product.id}">
                        <div class="rec-img">${product.image}</div>
                        <div class="rec-name">${product.name}</div>
                        <div class="rec-price">${product.price} تومان</div>
                        <span class="rec-badge">${product.badge}</span>
                        <button class="btn-rec-add" data-product-id="${product.id}">
                            <i class="fas fa-shopping-cart"></i> افزودن
                        </button>
                    </div>
                `;
            });

            container.innerHTML = html;

            container.querySelectorAll('.btn-rec-add').forEach(btn => {
                btn.addEventListener('click', function() {
                    const productId = parseInt(this.dataset.productId);
                    const product = recommendedProducts.find(p => p.id === productId);
                    if (product) {
                        let cart = JSON.parse(localStorage.getItem('zamaniCart')) || [];
                        const existing = cart.find(c => c.id === productId);
                        if (existing) {
                            existing.quantity = (existing.quantity || 1) + 1;
                        } else {
                            cart.push({
                                id: productId,
                                name: product.name,
                                price: parseInt(product.price.replace(/,/g, '')),
                                image: product.image,
                                quantity: 1,
                                type: 'package'
                            });
                        }
                        localStorage.setItem('zamaniCart', JSON.stringify(cart));
                        
                        if (window.dashboard) {
                            window.dashboard.renderCartStatus();
                        }
                        
                        window.dashboard.showToast(`🛒 ${product.name} به سبد خرید اضافه شد`, 'success');
                    }
                });
            });

        } else {
            container.innerHTML = `
                <div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-star" style="font-size:40px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ محصول پیشنهادی موجود نیست.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای دریافت پیشنهادات بهتر، محصولات بیشتری به <a href="index.html" style="color:var(--mustard-yellow);">علاقه‌مندی‌ها</a> اضافه کنید.
                    </p>
                </div>
            `;
        }
    }

    // ========================================
    // رندر کوپن‌ها (واقعی از سمت منشی)
    // ========================================
    renderCoupons() {
        const container = document.getElementById('couponGrid');
        if (!container) return;

        container.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-gray);">
                <i class="fas fa-spinner fa-spin" style="font-size:36px;display:block;margin-bottom:10px;"></i>
                <p>در حال بارگذاری کوپن‌ها...</p>
            </div>
        `;
        if (typeof apiGet !== 'function') {
            this.renderCouponsEmpty(container);
            return;
        }

        apiGet('products/discounts/?active=true').then(res => {
            let list = [];
            if (res && res.success) {
                list = Array.isArray(res.data) ? res.data :
                       (res.data && Array.isArray(res.data.results) ? res.data.results : []);
            }
            this.renderCouponsList(container, list);
        }).catch(() => {
            this.renderCouponsEmpty(container);
        });
    }

    renderCouponsList(container, list) {
        if (!list || list.length === 0) {
            this.renderCouponsEmpty(container);
            return;
        }

        const usedCodes = JSON.parse(localStorage.getItem('zamaniUsedCoupons') || '[]');

        container.innerHTML = list.map(coupon => {
            const code = coupon.code || '';
            const percent = coupon.percent || 0;
            const product = coupon.product_name || '';
            const endDate = coupon.end_date || '—';
            const isUsed = usedCodes.indexOf(code) !== -1;
            return `
                <div class="coupon-card" data-code="${code}">
                    <div class="coupon-code">${code}</div>
                    <div class="coupon-amount">${percent}٪ تخفیف</div>
                    <div class="coupon-expiry">
                        <i class="fas fa-box"></i> ${product}
                    </div>
                    <div class="coupon-expiry">
                        <i class="fas fa-calendar"></i> اعتبار تا: ${endDate}
                    </div>
                    <div class="coupon-status ${isUsed ? 'used' : 'active'}">
                        ${isUsed ? '✅ استفاده شده' : '✅ فعال'}
                    </div>
                    <button class="btn-use-coupon" data-code="${code}" ${isUsed ? 'disabled' : ''}>
                        ${isUsed ? 'استفاده شد' : 'استفاده از کوپن'}
                    </button>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.btn-use-coupon:not([disabled])').forEach(btn => {
            btn.addEventListener('click', function() {
                const code = this.dataset.code;
                let usedCodes = JSON.parse(localStorage.getItem('zamaniUsedCoupons') || '[]');
                if (usedCodes.indexOf(code) === -1) usedCodes.push(code);
                localStorage.setItem('zamaniUsedCoupons', JSON.stringify(usedCodes));
                this.textContent = 'استفاده شد';
                this.disabled = true;
                const card = this.closest('.coupon-card');
                const st = card.querySelector('.coupon-status');
                if (st) { st.textContent = '✅ استفاده شده'; st.className = 'coupon-status used'; }
                if (typeof showAlert === 'function') {
                    showAlert(`🎫 کد تخفیف "${code}" با موفقیت اعمال شد!`, 'success');
                }
            });
        });

        const badge = document.querySelector('.menu-item[data-section="coupons"] .menu-badge');
        if (badge) badge.textContent = list.length;
    }

    renderCouponsEmpty(container) {
        container.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-gray);">
                <i class="fas fa-tags" style="font-size:40px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                <p>هیچ کوپن تخفیفی دریافت نکرده‌اید.</p>
                <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                    کدهای تخفیف توسط پخش‌کننده اعمال می‌شوند.
                </p>
            </div>
        `;
        const badge = document.querySelector('.menu-item[data-section="coupons"] .menu-badge');
        if (badge) badge.textContent = 0;
    }

    // ========================================
    // رندر پیگیری سفارش
    // ========================================
    renderTracking() {
        const container = document.getElementById('trackingStepsContainer');
        const statusBadge = document.getElementById('trackingStatusBadge');
        const orderIdEl = document.querySelector('.tracking-header-section .order-id');
        const orderDateEl = document.querySelector('.tracking-header-section .order-date');
        const trackingCodeEl = document.querySelector('.tracking-footer-section .tracking-code');
        const trackingItemsEl = document.querySelector('.tracking-footer-section .tracking-items');
        const deliverBtn = document.getElementById('deliverBtn');

        if (!container) return;

        const trackingOrderId = localStorage.getItem('zamaniTrackingOrderId');
        let order = null;

        if (trackingOrderId) {
            order = this.recentOrders.find(o => o.id === parseInt(trackingOrderId));
        }

        if (!order && this.recentOrders && this.recentOrders.length > 0) {
            order = this.recentOrders[0];
            localStorage.setItem('zamaniTrackingOrderId', order.id.toString());
        }

        if (order) {
            if (orderIdEl) orderIdEl.textContent = `#${order.id}`;
            if (orderDateEl) {
                const date = this.formatDate(order.created_at);
                orderDateEl.innerHTML = `<i class="fas fa-calendar-alt"></i> ${date}`;
            }

            if (trackingCodeEl) {
                trackingCodeEl.textContent = order.tracking_code || '—';
            }

            if (trackingItemsEl) {
                const items = Array.isArray(order.items) ? order.items : [];
                const totalItems = items.reduce((sum, it) => sum + (parseInt(it.quantity) || 0), 0);
                trackingItemsEl.textContent = totalItems > 0 ? totalItems.toLocaleString('fa-IR') + ' قلم' : '—';
            }

            const status = order.status || 'PENDING';
            const statusMap = {
                'PENDING': { step: 0, text: 'در انتظار تایید', class: 'preparing', icon: 'fa-clock' },
                'AWAITING_APPROVAL': { step: 0, text: 'در انتظار تأیید پخش‌کننده', class: 'preparing', icon: 'fa-user-clock' },
                'CONFIRMED': { step: 1, text: 'تایید شده', class: 'preparing', icon: 'fa-check-circle' },
                'PROCESSING': { step: 1, text: 'در حال آماده‌سازی', class: 'preparing', icon: 'fa-boxes' },
                'PREPARING': { step: 1, text: 'در حال آماده‌سازی', class: 'preparing', icon: 'fa-boxes' },
                'SHIPPED': { step: 2, text: 'در حال ارسال', class: 'shipping', icon: 'fa-truck fa-pulse' },
                'DELIVERED': { step: 3, text: 'تحویل داده شده', class: 'delivered', icon: 'fa-check-circle' },
                'COMPLETED': { step: 4, text: 'تکمیل شده', class: 'completed', icon: 'fa-check-double' },
                'CANCELLED': { step: 0, text: 'لغو شده', class: 'preparing', icon: 'fa-times-circle' }
            };

            const statusInfo = statusMap[status] || statusMap['PENDING'];
            const currentStep = statusInfo.step;

            if (statusBadge) {
                statusBadge.innerHTML = `<i class="fas ${statusInfo.icon}"></i> ${statusInfo.text}`;
                statusBadge.className = `tracking-status-badge ${statusInfo.class}`;
            }

            const steps = container.querySelectorAll('.tracking-step-horizontal');
            const connectors = container.querySelectorAll('.tracking-connector');

            const orderSteps = [
                { label: 'ثبت سفارش', desc: 'سفارش ثبت شد', icon: 'fa-clipboard-list' },
                { label: 'آماده‌سازی', desc: 'در حال بسته‌بندی', icon: 'fa-boxes' },
                { label: 'ارسال', desc: 'ارسال به مقصد', icon: 'fa-truck' },
                { label: 'تحویل', desc: 'دریافت توسط مشتری', icon: 'fa-home' }
            ];

            steps.forEach((el, index) => {
                const stepNum = index + 1;
                el.classList.remove('done', 'active');
                
                if (stepNum < currentStep + 1) {
                    el.classList.add('done');
                } else if (stepNum === currentStep + 1 && currentStep < 4) {
                    el.classList.add('active');
                }

                const stepData = orderSteps[index] || orderSteps[0];
                const iconEl = el.querySelector('.step-circle i');
                const labelEl = el.querySelector('.step-label');
                const descEl = el.querySelector('.step-desc');
                const timeEl = el.querySelector('.step-time');

                if (iconEl) {
                    iconEl.className = `fas ${stepData.icon}`;
                }
                if (labelEl) labelEl.textContent = stepData.label;
                if (descEl) descEl.textContent = stepData.desc;
                if (timeEl) {
                    if (stepNum <= currentStep) {
                        timeEl.textContent = this.formatDate(order.created_at);
                    } else if (stepNum === currentStep + 1) {
                        timeEl.textContent = 'در حال انجام...';
                    } else {
                        timeEl.textContent = 'در انتظار';
                    }
                }
            });

            connectors.forEach((el, index) => {
                const connectorIndex = index + 1;
                el.classList.remove('done', 'partial');
                if (connectorIndex <= currentStep) {
                    el.classList.add('done');
                } else if (connectorIndex === currentStep + 1 && currentStep < 3) {
                    el.classList.add('partial');
                }
            });

            if (deliverBtn) {
                if (currentStep >= 3) {
                    deliverBtn.disabled = true;
                    deliverBtn.innerHTML = '<i class="fas fa-check-double"></i> تحویل گرفته شد';
                    deliverBtn.className = 'deliver-btn done';
                } else {
                    deliverBtn.disabled = false;
                    deliverBtn.innerHTML = '<i class="fas fa-check-circle"></i> تحویل گرفتم';
                    deliverBtn.className = 'deliver-btn';
                    deliverBtn.onclick = async function() {
                        if (!order) return;
                        if (confirm('آیا از دریافت سفارش مطمئن هستید؟')) {
                            try {
                                const response = await apiPost(`orders/${order.id}/confirm_delivery/`);
                                if (response.success) {
                                    showAlert('✅ سفارش با موفقیت تحویل گرفته شد', 'success');
                                    await window.dashboard.loadRecentOrders();
                                    window.dashboard.renderTracking();
                                    window.dashboard.renderFinancial();
                                } else {
                                    showAlert('❌ خطا در تایید دریافت سفارش: ' + (response.data?.error || response.data?.detail || 'خطا'), 'error');
                                }
                            } catch (err) {
                                showAlert('❌ خطا در ارتباط با سرور', 'error');
                            }
                        }
                    };
                }
            }

        } else {
            if (orderIdEl) orderIdEl.textContent = '—';
            if (orderDateEl) orderDateEl.innerHTML = '<i class="fas fa-calendar-alt"></i> —';
            if (trackingCodeEl) trackingCodeEl.textContent = '—';
            if (trackingItemsEl) trackingItemsEl.textContent = '—';
            if (statusBadge) {
                statusBadge.innerHTML = '<i class="fas fa-box-open"></i> بدون سفارش';
                statusBadge.className = 'tracking-status-badge preparing';
            }
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-box-open" style="font-size:48px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ سفارشی برای پیگیری وجود ندارد.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای پیگیری سفارش، ابتدا یک سفارش ثبت کنید.
                    </p>
                </div>
            `;
        }
    }

    // ========================================
    // رندر مرجوعی
    // ========================================
    renderReturns() {
        const container = document.getElementById('returnList');
        if (!container) return;

        const returns = this.returnRequests || [];

        if (returns && returns.length > 0) {
            let html = '';
            returns.forEach(item => {
                const statusLabels = {
                    'PENDING': '⏳ در انتظار بررسی',
                    'APPROVED': '✅ تایید شده',
                    'REJECTED': '❌ رد شده',
                    'COMPLETED': '✅ تکمیل شده',
                    'CANCELLED': '❌ لغو شده'
                };
                
                const statusClass = {
                    'PENDING': 'pending',
                    'APPROVED': 'approved',
                    'REJECTED': 'rejected',
                    'COMPLETED': 'completed',
                    'CANCELLED': 'rejected'
                };

                const reasonLabels = {
                    'DEFECTIVE': 'محصول معیوب است',
                    'WRONG': 'محصول اشتباه ارسال شده',
                    'DAMAGED': 'آسیب دیده در حمل و نقل',
                    'EXPIRED': 'تاریخ انقضا گذشته',
                    'OTHER': 'سایر موارد'
                };

                html += `
                    <div class="return-item" data-id="${item.id}">
                        <div class="return-info">
                            <div class="return-title">سفارش #${item.order_number} - ${item.product_name}</div>
                            <div class="return-meta">
                                <span><i class="fas fa-calendar"></i> ${this.formatDate(item.created_at)}</span>
                                <span><i class="fas fa-info-circle"></i> دلیل: ${reasonLabels[item.reason] || item.reason}</span>
                                <span><i class="fas fa-exchange-alt" style="color:var(--mustard-yellow);"></i> تعداد: ${item.quantity}</span>
                            </div>
                        </div>
                        <span class="return-status ${statusClass[item.status] || 'pending'}">
                            ${statusLabels[item.status] || item.status}
                        </span>
                        <button class="btn-view-return" data-id="${item.id}">مشاهده</button>
                    </div>
                `;
            });

            container.innerHTML = html;

            container.querySelectorAll('.btn-view-return').forEach(btn => {
                btn.addEventListener('click', function() {
                    const id = parseInt(this.dataset.id);
                    const item = returns.find(r => r.id === id);
                    if (item) {
                        const reasonLabels = {
                            'DEFECTIVE': 'محصول معیوب است',
                            'WRONG': 'محصول اشتباه ارسال شده',
                            'DAMAGED': 'آسیب دیده در حمل و نقل',
                            'EXPIRED': 'تاریخ انقضا گذشته',
                            'OTHER': 'سایر موارد'
                        };
                        const statusLabels = {
                            'PENDING': 'در انتظار بررسی',
                            'APPROVED': 'تایید شده',
                            'REJECTED': 'رد شده',
                            'COMPLETED': 'تکمیل شده',
                            'CANCELLED': 'لغو شده'
                        };
                        alert(`📋 جزئیات درخواست مرجوعی:\n\n` +
                              `سفارش: #${item.order_number}\n` +
                              `محصول: ${item.product_name}\n` +
                              `تعداد: ${item.quantity}\n` +
                              `دلیل: ${reasonLabels[item.reason] || item.reason}\n` +
                              `توضیحات: ${item.description || 'ندارد'}\n` +
                              `تاریخ: ${this.formatDate(item.created_at)}\n` +
                              `وضعیت: ${statusLabels[item.status] || item.status}`);
                    }
                });
            });

        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-undo-alt" style="font-size:40px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ درخواست مرجوعی ثبت نشده است.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای ثبت درخواست مرجوعی، روی دکمه "درخواست جدید" کلیک کنید.
                    </p>
                </div>
            `;
        }
    }

    // ========================================
    // رندر چک‌ها - فقط از API واقعی
    // ========================================
    renderCheques() {
        const tbody = document.getElementById('chequeTableBody');
        if (!tbody) return;

        const cheques = this.cheques || [];

        if (cheques && cheques.length > 0) {
            let html = '';
            let totalCashed = 0;
            let totalPending = 0;

            cheques.forEach(cheque => {
                const statusLabels = {
                    'PENDING': 'در انتظار بررسی',
                    'APPROVED': 'تایید شده',
                    'REJECTED': 'رد شده',
                    'PAID': 'پرداخت شده'
                };
                
                const statusClass = {
                    'PENDING': 'pending',
                    'APPROVED': 'approved',
                    'REJECTED': 'rejected',
                    'PAID': 'paid'
                };

                if (cheque.status === 'PAID' || cheque.status === 'APPROVED') {
                    totalCashed += Number(cheque.amount);
                } else {
                    totalPending += Number(cheque.amount);
                }

                const info = (cheque.customer_info && typeof cheque.customer_info === 'object')
                    ? cheque.customer_info
                    : (cheque.customer && typeof cheque.customer === 'object' ? cheque.customer : null);
                const issuer = info?.company_name || info?.full_name || cheque.customer_name || '---';
                const regBy = cheque.registered_by_label || (cheque.registered_by === 'CUSTOMER' ? 'مشتری' : 'منشی');
                const imageCell = cheque.image
                    ? `<a href="${this.chequeMediaUrl(cheque.image)}" target="_blank" rel="noopener" title="مشاهده تصویر چک"><img src="${this.chequeMediaUrl(cheque.image)}" alt="چک" style="width:52px;height:34px;object-fit:cover;border-radius:6px;border:1px solid rgba(255,255,255,0.1);" /></a>`
                    : '<span style="color:var(--text-gray);font-size:12px;">—</span>';
                const deleteBtn = cheque.status === 'PENDING'
                    ? `<button class="btn-danger btn-sm delete-cheque" data-id="${cheque.id}" title="حذف چک"><i class="fas fa-trash"></i></button>`
                    : '';
                const actions = `<button class="btn-secondary btn-sm view-cheque" data-id="${cheque.id}">جزئیات</button> ${deleteBtn}`;

                html += `
                    <tr data-status="${cheque.status}">
                        <td>${cheque.check_number}</td>
                        <td>${this.formatDate(cheque.issue_date)}</td>
                        <td>${this.formatPrice(cheque.amount)}</td>
                        <td>${cheque.bank_name}</td>
                        <td>${issuer}</td>
                        <td>${this.formatDate(cheque.due_date)}</td>
                        <td><span class="cheque-status-badge ${statusClass[cheque.status] || 'pending'}">${cheque.status_label || statusLabels[cheque.status] || cheque.status}</span></td>
                        <td>${regBy}</td>
                        <td>${imageCell}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;

            // به‌روزرسانی آمار
            const total = cheques.length;
            const cashed = cheques.filter(c => c.status === 'PAID' || c.status === 'APPROVED').length;
            const pending = cheques.filter(c => c.status === 'PENDING').length;
            const rejected = cheques.filter(c => c.status === 'REJECTED').length;
            
            const totalEl = document.getElementById('chequeTotalCount');
            const cashedEl = document.getElementById('chequeCashedCount');
            const pendingEl = document.getElementById('chequePendingCount');
            const postdatedEl = document.getElementById('chequePostdatedCount');
            const totalAmountEl = document.getElementById('chequeTotalAmount');
            const cashedAmountEl = document.getElementById('chequeCashedAmount');
            const pendingAmountEl = document.getElementById('chequePendingAmount');
            const badgeEl = document.getElementById('chequeCountBadge');
            
            if (totalEl) totalEl.textContent = total;
            if (cashedEl) cashedEl.textContent = cashed;
            if (pendingEl) pendingEl.textContent = pending;
            if (postdatedEl) postdatedEl.textContent = rejected;
            if (totalAmountEl) totalAmountEl.textContent = this.formatPrice(totalCashed + totalPending);
            if (cashedAmountEl) cashedAmountEl.textContent = this.formatPrice(totalCashed);
            if (pendingAmountEl) pendingAmountEl.textContent = this.formatPrice(totalPending);
            if (badgeEl) badgeEl.textContent = total;

            // رویداد مشاهده جزئیات
            tbody.querySelectorAll('.view-cheque').forEach(btn => {
                btn.addEventListener('click', function() {
                    const id = parseInt(this.dataset.id);
                    const cheque = cheques.find(c => c.id === id);
                    if (cheque) {
                        const statusLabels = {
                            'PENDING': 'در انتظار بررسی',
                            'APPROVED': 'تایید شده',
                            'REJECTED': 'رد شده',
                            'PAID': 'پرداخت شده'
                        };
alert(`📋 جزئیات چک:\n\n` +
                              `شماره: ${cheque.check_number}\n` +
                              `مبلغ: ${this.formatPrice(cheque.amount)}\n` +
                              `بانک: ${cheque.bank_name}\n` +
                              `صاحب چک: ${issuer}\n` +
                              `تاریخ صدور: ${this.formatDate(cheque.issue_date)}\n` +
                              `تاریخ سررسید: ${this.formatDate(cheque.due_date)}\n` +
                              `ثبت توسط: ${regBy}\n` +
                              `وضعیت: ${statusLabels[cheque.status] || cheque.status}`);
                }
            });
        });

        // رویداد حذف چک (فقط چکهای در انتظار)
        tbody.querySelectorAll('.delete-cheque').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = parseInt(this.dataset.id);
                const cheque = cheques.find(c => c.id === id);
                if (!cheque) return;
                const dash = window.dashboard;
                const amountText = dash ? dash.formatPrice(cheque.amount) : String(Number(cheque.amount).toLocaleString('fa-IR') + ' تومان');
                if (confirm('آیا از حذف این چک اطمینان دارید؟\n' + (cheque.check_number || '') + ' — ' + amountText)) {
                    const res = await apiDelete(`finance/checks/${id}/`);
                    if (res.success) {
                        if (dash) {
                            await dash.loadCheques();
                            dash.renderCheques();
                        }
                        dash?.showToast('چک با موفقیت حذف شد', 'success');
                    } else {
                        dash?.showToast('خطا در حذف چک: ' + (res.data?.detail || res.data?.error || 'خطا'), 'error');
                    }
                }
            });
        });

        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align:center;padding:30px;color:var(--text-gray);">
                        <i class="fas fa-money-check-alt" style="font-size:24px;display:block;margin-bottom:10px;color:var(--mustard-yellow);"></i>
                        هیچ چکی ثبت نشده است.
                        <br>
                        <span style="font-size:12px;margin-top:8px;display:block;color:var(--text-gray);">
                            برای ثبت چک جدید، روی دکمه "افزودن چک" کلیک کنید.
                        </span>
                    </td>
                </tr>
            `;

            const totalEl = document.getElementById('chequeTotalCount');
            const cashedEl = document.getElementById('chequeCashedCount');
            const pendingEl = document.getElementById('chequePendingCount');
            const postdatedEl = document.getElementById('chequePostdatedCount');
            const totalAmountEl = document.getElementById('chequeTotalAmount');
            const cashedAmountEl = document.getElementById('chequeCashedAmount');
            const pendingAmountEl = document.getElementById('chequePendingAmount');
            const badgeEl = document.getElementById('chequeCountBadge');

            if (totalEl) totalEl.textContent = '۰';
            if (cashedEl) cashedEl.textContent = '۰';
            if (pendingEl) pendingEl.textContent = '۰';
            if (postdatedEl) postdatedEl.textContent = '۰';
            if (totalAmountEl) totalAmountEl.textContent = this.formatPrice(0);
            if (cashedAmountEl) cashedAmountEl.textContent = this.formatPrice(0);
            if (pendingAmountEl) pendingAmountEl.textContent = this.formatPrice(0);
            if (badgeEl) badgeEl.textContent = '۰';
        }
    }

    // ========================================
    // بارگذاری تیکت‌ها
    // ========================================
    async loadTickets() {
        const response = await apiGet('tickets/');
        if (response.success) {
            this.tickets = response.data.results || response.data || [];
            console.log('🎫 Tickets:', this.tickets);
            return this.tickets;
        } else {
            console.warn('⚠️ خطا در دریافت تیکت‌ها');
            this.tickets = [];
            return [];
        }
    }

    // ========================================
    // رندر تیکت‌ها
    // ========================================
    renderTickets() {
        const container = document.getElementById('ticketList');
        if (!container) return;

        const tickets = this.tickets || [];
        this.updateTicketStats();

        if (tickets && tickets.length > 0) {
            let html = '';
            tickets.forEach(ticket => {
                const preview = (() => {
                    const msgs = Array.isArray(ticket.messages) && ticket.messages.length
                        ? ticket.messages
                        : (ticket.admin_reply || ticket.customer_reply
                            ? [{ sender: (ticket.admin_reply ? 'STAFF' : 'CUSTOMER'), text: ticket.admin_reply || ticket.customer_reply }]
                            : [{ sender: 'CUSTOMER', text: ticket.message || '' }]);
                    const last = msgs[msgs.length - 1];
                    return { text: last.text || '', isStaff: last.sender === 'STAFF' };
                })();

                const statusLabels = {
                    'OPEN': 'باز',
                    'ANSWERED': 'پاسخ داده شده',
                    'CLOSED': 'بسته شده'
                };
                
                const statusClass = {
                    'OPEN': 'processing',
                    'ANSWERED': 'answered',
                    'CLOSED': 'canceled'
                };

                const categoryLabels = {
                    'GENERAL': 'عمومی',
                    'ORDER': 'مشکل سفارش',
                    'PRODUCT': 'سوال درباره محصول',
                    'DELIVERY': 'مشکل ارسال',
                    'PAYMENT': 'مشکل پرداخت',
                    'TECHNICAL': 'مشکل فنی',
                    'SUGGESTION': 'پیشنهاد',
                    'COMPLAINT': 'شکایت'
                };

                html += `
                    <div class="ticket-item" data-ticket="${ticket.id}" data-status="${ticket.status}">
                        <div class="ticket-info">
                            <div class="ticket-title">
                                <i class="fas fa-tag"></i> ${ticket.title}
                            </div>
                            <div class="ticket-meta">
                                <span><i class="fas fa-calendar"></i> ${this.formatDate(ticket.created_at)}</span>
                                <span><i class="fas fa-folder"></i> ${categoryLabels[ticket.category] || ticket.category}</span>
                                <span class="status-badge ${statusClass[ticket.status] || 'processing'}" style="font-size:10px;padding:1px 10px;">
                                    ${statusLabels[ticket.status] || ticket.status}
                                </span>
                            </div>
                            <div style="font-size:13px;color:var(--text-gray);margin-top:4px;max-width:80%;">
                                ${(ticket.message || '').length > 100 ? (ticket.message || '').substring(0, 100) + '...' : (ticket.message || '')}
                            </div>
                            ${preview.isStaff ? `
                                <div style="font-size:12px;color:#4CAF50;margin-top:4px;padding:6px 10px;background:rgba(76,175,80,0.1);border-radius:8px;border-right:3px solid #4CAF50;">
                                    <i class="fas fa-reply"></i> پاسخ: ${preview.text.length > 80 ? preview.text.substring(0, 80) + '...' : preview.text}
                                </div>
                            ` : ''}
                        </div>
                        <div class="ticket-actions">
                            <button class="btn-secondary btn-sm view-ticket" data-ticket="${ticket.id}">مشاهده</button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            container.querySelectorAll('.view-ticket').forEach(btn => {
                btn.addEventListener('click', function() {
                    const id = parseInt(this.dataset.ticket);
                    const ticket = tickets.find(t => t.id === id);
                    if (ticket) {
                        openTicketDetail(ticket);
                    }
                });
            });

        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-ticket-alt" style="font-size:48px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ تیکتی ثبت نشده است.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای ارسال تیکت، روی دکمه "تیکت جدید" کلیک کنید.
                    </p>
                </div>
            `;
        }
    }

    // ========================================
    // آمار تیکت‌ها
    // ========================================
    updateTicketStats() {
        const tickets = this.tickets || [];
        const total = tickets.length;
        const answered = tickets.filter(t => t.status === 'ANSWERED').length;
        const open = tickets.filter(t => t.status === 'OPEN').length;
        const closed = tickets.filter(t => t.status === 'CLOSED').length;

        const stats = document.querySelectorAll('.ticket-stat-item .number');
        if (stats[0]) stats[0].textContent = total;
        if (stats[1]) stats[1].textContent = answered;
        if (stats[2]) stats[2].textContent = open;
        if (stats[3]) stats[3].textContent = closed;

        const badge = document.getElementById('ticketCountBadge');
        if (badge) badge.textContent = total;
    }

    // ========================================
    // بارگذاری اعلان‌ها
    // ========================================
    async loadNotifications() {
        const response = await apiGet('notifications/');
        if (response.success) {
            this.notifications = response.data.results || response.data || [];
            console.log('🔔 Notifications:', this.notifications);
            return this.notifications;
        } else {
            console.warn('⚠️ خطا در دریافت اعلان‌ها');
            this.notifications = [];
            return [];
        }
    }

    // ========================================
    // رندر اعلان‌ها
    // ========================================
    renderNotifications() {
        const container = document.getElementById('notifList');
        if (!container) return;

        const notifications = this.notifications || [];

        if (notifications.length > 0) {
            let html = '';
            notifications.forEach(notif => {
                const typeIcon = {
                    'INFO': 'fa-info-circle',
                    'OFFER': 'fa-tag',
                    'WARNING': 'fa-exclamation-triangle',
                    'MESSAGE': 'fa-envelope'
                }[notif.type] || 'fa-bell';

                const isRead = notif.is_read ? 'read' : 'unread';
                
                html += `
                    <div class="notif-item ${isRead}" data-id="${notif.id}" style="${notif.is_read ? 'opacity:0.6;' : ''}">
                        <span class="notif-text">
                            <i class="fas ${typeIcon}"></i>
                            <strong>${notif.title}</strong>
                            <span style="color:var(--text-gray);font-weight:400;display:block;font-size:12px;margin-top:4px;">${notif.message}</span>
                        </span>
                        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
                            <span class="notif-time">${this.formatDate(notif.created_at)}</span>
                            <div style="display:flex;gap:4px;">
                                ${!notif.is_read ? `<button class="btn-mark-read btn-secondary btn-sm" data-id="${notif.id}">خوانده شد</button>` : ''}
                                <button class="btn-delete-notif btn-secondary btn-sm" data-id="${notif.id}" style="border-color:#e74c3c;color:#e74c3c;">حذف</button>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            // رویداد Mark as Read
            container.querySelectorAll('.btn-mark-read').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.stopPropagation();
                    const id = this.dataset.id;
                    await window.dashboard.markNotificationAsRead(id);
                });
            });

            // رویداد Delete
            container.querySelectorAll('.btn-delete-notif').forEach(btn => {
                btn.addEventListener('click', async function(e) {
                    e.stopPropagation();
                    const id = this.dataset.id;
                    await window.dashboard.deleteNotification(id);
                });
            });

        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-bell-slash" style="font-size:48px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>هیچ اعلانی وجود ندارد.</p>
                </div>
            `;
        }

        // به‌روزرسانی تعداد اعلان‌های خوانده نشده
        this.updateNotificationBadge();
    }

    // ========================================
    // علامت زدن یک اعلان به عنوان خوانده شده
    // ========================================
    async markNotificationAsRead(id) {
        const response = await apiPost(`notifications/${id}/mark_as_read/`);
        if (response.success) {
            await this.loadNotifications();
            this.renderNotifications();
            showAlert('✅ اعلان به عنوان خوانده شده علامت‌گذاری شد', 'success');
        } else {
            showAlert('❌ خطا در علامت‌گذاری اعلان', 'error');
        }
    }

    // ========================================
    // علامت زدن همه به عنوان خوانده شده
    // ========================================
    async markAllNotificationsAsRead() {
        const response = await apiPost('notifications/mark_all_as_read/');
        if (response.success) {
            await this.loadNotifications();
            this.renderNotifications();
            showAlert('✅ همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند', 'success');
        } else {
            showAlert('❌ خطا در علامت‌گذاری همه اعلان‌ها', 'error');
        }
    }

    // ========================================
    // حذف یک اعلان
    // ========================================
    async deleteNotification(id) {
        if (!confirm('آیا از حذف این اعلان مطمئن هستید؟')) return;
        
        const response = await apiPost(`notifications/${id}/delete_notification/`);
        if (response.success) {
            await this.loadNotifications();
            this.renderNotifications();
            showAlert('🗑️ اعلان حذف شد', 'success');
        } else {
            showAlert('❌ خطا در حذف اعلان', 'error');
        }
    }

    // ========================================
    // به‌روزرسانی تعداد اعلان‌های خوانده نشده
    // ========================================
    updateNotificationBadge() {
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            const unreadCount = (this.notifications || []).filter(n => !n.is_read).length;
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
        }
    }

    // ========================================
    // رندر سفارش‌ها
    // ========================================
    renderRecentOrders() {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        if (this.recentOrders && this.recentOrders.length > 0) {
            let html = '';
            let totalRemain = 0;

            this.recentOrders.forEach((order) => {
                const paid = order.paid_amount || 0;
                const total = (order.total_price || order.total_amount || 0);
                const remain = this.orderOutstanding(order);
                totalRemain += remain;

                let productNames = [];
                if (order.items && order.items.length > 0) {
                    productNames = order.items.map(item => {
                        return item.product?.name || item.product_name || item.name || 'محصول';
                    });
                }
                
                let description = 'بدون محصول';
                if (productNames.length === 1) {
                    description = productNames[0];
                } else if (productNames.length === 2) {
                    description = `${productNames[0]} و ${productNames[1]}`;
                } else if (productNames.length > 2) {
                    description = `${productNames[0]}، ${productNames[1]} و ${productNames.length - 2} مورد دیگر`;
                }

                html += `
                    <tr data-date="${this.formatDate(order.created_at)}" data-amount="${total}">
                        <td>#${order.id}</td>
                        <td>${this.formatDate(order.created_at)}</td>
                        <td>${description}</td>
                        <td>${this.formatPrice(total)}</td>
                        <td><span class="status-badge ${remain === 0 ? 'paid' : remain > 0 ? 'partial' : 'unpaid'}">${this.formatPrice(paid)}</span></td>
                        <td><span class="remain-amount ${remain === 0 ? 'zero' : 'positive'}">${this.formatPrice(remain)}</span></td>
                        <td><span class="payment-method ${order.payment_method || 'cash'}">${this.getPaymentMethodLabel(order.payment_method)}</span></td>
                        <td><span class="status-badge ${order.status}">${this.getStatusLabel(order.status)}</span></td>
                        <td>
                            <button class="btn-secondary btn-sm track-order" data-order-id="${order.id}">
                                <i class="fas fa-map-pin"></i> پیگیری
                            </button>
                            <button class="btn-secondary btn-sm print-order" data-order-id="${order.id}">
                                <i class="fas fa-print"></i> چاپ
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += `
                <tr class="total-remain-row">
                    <td colspan="4" style="text-align:center;color:var(--mustard-yellow);">
                        <i class="fas fa-calculator"></i> جمع کل مانده حساب‌ها
                    </td>
                    <td colspan="6" style="color:var(--mustard-yellow);">
                        <span style="font-size:15px;font-weight:800;" id="ordersTotalRemain">${this.formatPrice(totalRemain)}</span>
                        <span style="font-size:11px;color:var(--text-gray);margin-right:12px;" id="ordersTotalCount">(${this.recentOrders.length} سفارش)</span>
                    </td>
                </tr>
            `;

            tbody.innerHTML = html;
            this.updateOrderStats();

            document.querySelectorAll('.track-order').forEach(btn => {
                btn.addEventListener('click', function() {
                    const orderId = this.dataset.orderId;
                    localStorage.setItem('zamaniTrackingOrderId', orderId);
                    
                    const trackingMenuItem = document.querySelector('.menu-item[data-section="tracking"]');
                    if (trackingMenuItem) {
                        trackingMenuItem.click();
                    }
                    
                    if (window.dashboard) {
                        window.dashboard.renderTracking();
                    }
                    
                    window.dashboard.showToast(`📦 سفارش #${orderId} برای پیگیری انتخاب شد`, 'success');
                });
            });

        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align:center;padding:30px;color:var(--text-gray);">
                        <i class="fas fa-inbox" style="font-size:24px;display:block;margin-bottom:10px;color:var(--mustard-yellow);"></i>
                        هنوز سفارشی ثبت نشده است.
                    </td>
                </tr>
            `;
        }

        document.querySelectorAll('.print-order').forEach(btn => {
            btn.addEventListener('click', function() {
                const orderId = this.dataset.orderId;
                alert(`🖨️ درخواست چاپ فاکتور برای سفارش #${orderId}`);
            });
        });
    }

    // ========================================
    // رندر سبد خرید
    // ========================================
    renderCartStatus() {
        const container = document.getElementById('cartItemsList');
        const totalEl = document.getElementById('cartTotalAmount');
        const badge = document.getElementById('cartCountBadge');

        if (!container) return;

        let cartItems = JSON.parse(localStorage.getItem('zamaniCart')) || [];
        
        if (cartItems.length === 0 && this.cartData) {
            cartItems = this.cartData.results || this.cartData.items || [];
        }

        if (!document.getElementById('cartTypeStyles')) {
            const style = document.createElement('style');
            style.id = 'cartTypeStyles';
            style.textContent = `
                .item-type {
                    font-size: 11px;
                    padding: 2px 10px;
                    border-radius: 20px;
                    display: inline-block;
                    width: fit-content;
                }
                .item-type.package-badge {
                    background: rgba(201, 160, 61, 0.15);
                    color: #c9a03d;
                    border: 1px solid rgba(201, 160, 61, 0.3);
                }
                .item-type.cartoon-badge {
                    background: rgba(230, 126, 34, 0.15);
                    color: #e67e22;
                    border: 1px solid rgba(230, 126, 34, 0.3);
                }
                .cart-item-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .cart-item-row .item-info {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                    flex: 1;
                    min-width: 120px;
                }
                .cart-item-row .item-name {
                    font-size: 14px;
                    color: var(--text-light);
                }
                .cart-item-row .item-qty {
                    font-size: 13px;
                    color: var(--text-gray);
                }
                .cart-item-row .item-price {
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--mustard-yellow);
                }
                .cart-item-row .item-actions {
                    display: flex;
                    gap: 6px;
                    align-items: center;
                }
                .cart-item-row .item-actions button {
                    padding: 2px 10px;
                    border-radius: 20px;
                    border: none;
                    font-size: 11px;
                    cursor: pointer;
                    transition: 0.3s;
                }
                .cart-item-row .item-actions .btn-qty-local {
                    background: rgba(255, 255, 255, 0.05);
                    color: var(--text-gray);
                }
                .cart-item-row .item-actions .btn-qty-local:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                .cart-item-row .item-actions .btn-remove-local {
                    background: rgba(231, 76, 60, 0.15);
                    color: #e74c3c;
                }
                .cart-item-row .item-actions .btn-remove-local:hover {
                    background: rgba(231, 76, 60, 0.25);
                }
                @media (max-width: 550px) {
                    .cart-item-row {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 6px;
                    }
                    .cart-item-row .item-info {
                        min-width: auto;
                    }
                    .cart-item-row .item-actions {
                        justify-content: flex-end;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        if (cartItems && cartItems.length > 0) {
            let total = 0;
            let totalQty = 0;

            let html = '';
            cartItems.forEach((item, index) => {
                const qty = item.quantity || 1;
                const price = item.price || item.unit_price || item.product?.price || 0;
                const name = item.name || item.product?.name || item.product_name || 'محصول';
                
                const type = item.type || 'package';
                const pack = (function() {
                    const explicit = parseInt(item.packPerCarton, 10);
                    if (explicit && explicit > 0) return explicit;
                    if (window.ZamaniProductMap && ZamaniProductMap.ready()) return ZamaniProductMap.packFor(item);
                    return 1;
                })();
                const packNote = pack > 1 ? ` (${String(pack).replace(/\d/g, function(d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; })} بسته)` : '';
                const typeLabel = type === 'cartoon' ? '🎬 کارتنی' + packNote : '📦 بسته‌ای';
                const typeClass = type === 'cartoon' ? 'cartoon-badge' : 'package-badge';
                
                const itemTotal = price * qty;
                total += itemTotal;
                totalQty += qty;

                html += `
                    <div class="cart-item-row">
                        <div class="item-info">
                            <span class="item-name">${name}</span>
                            <span class="item-type ${typeClass}">${typeLabel}</span>
                        </div>
                        <span class="item-qty">تعداد: ${qty}</span>
                        <span class="item-price">${this.formatPrice(itemTotal)}</span>
                        <div class="item-actions">
                            <button class="btn-qty-local" data-index="${index}" data-delta="-1"><i class="fas fa-minus"></i></button>
                            <button class="btn-qty-local" data-index="${index}" data-delta="1"><i class="fas fa-plus"></i></button>
                            <button class="btn-remove-local" data-index="${index}"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
            totalEl.textContent = this.formatPrice(total);
            if (badge) badge.textContent = totalQty;

            document.querySelectorAll('.btn-qty-local').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    const delta = parseInt(this.dataset.delta);
                    let items = JSON.parse(localStorage.getItem('zamaniCart')) || [];
                    if (items[index]) {
                        items[index].quantity = Math.max(1, (items[index].quantity || 1) + delta);
                        localStorage.setItem('zamaniCart', JSON.stringify(items));
                        if (window.dashboard) {
                            window.dashboard.renderCartStatus();
                        }
                    }
                });
            });

            document.querySelectorAll('.btn-remove-local').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.dataset.index);
                    if (confirm('آیا از حذف این محصول از سبد خرید مطمئن هستید؟')) {
                        let items = JSON.parse(localStorage.getItem('zamaniCart')) || [];
                        items.splice(index, 1);
                        localStorage.setItem('zamaniCart', JSON.stringify(items));
                        if (window.dashboard) {
                            window.dashboard.renderCartStatus();
                        }
                    }
                });
            });

        } else {
            container.innerHTML = `
                <div style="text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-shopping-cart" style="font-size:40px;color:var(--mustard-yellow);display:block;margin-bottom:10px;"></i>
                    <p>سبد خرید شما خالی است.</p>
                    <p style="font-size:12px;margin-top:8px;color:var(--text-gray);">
                        برای افزودن محصول به سبد خرید، به صفحه <a href="index.html" style="color:var(--mustard-yellow);">خانه</a> بروید.
                    </p>
                </div>
            `;
            totalEl.textContent = '۰ تومان';
            if (badge) badge.textContent = '0';
        }
    }

    // ========================================
    // آمار سفارش‌ها
    // ========================================
    updateOrderStats() {
        const rows = document.querySelectorAll('#ordersTableBody tr:not(.total-remain-row)');
        let todayTotal = 0, weekTotal = 0, monthTotal = 0, yearTotal = 0;
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const weekStart = new Date(today);
        const weekDay = (today.getDay() === 0) ? 6 : today.getDay() - 1;
        weekStart.setDate(weekStart.getDate() - weekDay);
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        const yearStart = new Date(today.getFullYear(), 0, 1);

        rows.forEach(row => {
            const dateAttr = row.getAttribute('data-date');
            const amountStr = row.getAttribute('data-amount') || row.querySelector('td:nth-child(4)')?.textContent.replace(/,/g, '').replace(' تومان', '');
            const amount = parseInt(amountStr) || 0;
            if (!dateAttr) return;
            const rowDate = this.parsePersianDate(dateAttr);
            if (!rowDate) return;
            if (rowDate >= today) todayTotal += amount;
            if (rowDate >= weekStart) weekTotal += amount;
            if (rowDate >= monthStart) monthTotal += amount;
            if (rowDate >= yearStart) yearTotal += amount;
        });

        const statMap = {
            'orderTodayTotal': todayTotal,
            'orderWeekTotal': weekTotal,
            'orderMonthTotal': monthTotal,
            'orderYearTotal': yearTotal
        };

        Object.entries(statMap).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = this.formatPrice(value);
        });
    }

    // ========================================
    // توابع کمکی
    // ========================================
    updateHeader() {
        if (!this.userData) return;
    }

    getRoleLabel(role) {
        const roles = {
            'CUSTOMER': 'مشتری',
            'DISTRIBUTOR': 'توزیع‌کننده',
            'SECRETARY': 'منشی',
            'ADMIN': 'مدیر',
            'OWNER': 'صاحب شرکت'
        };
        return roles[role] || role || 'کاربر';
    }

    getStatusLabel(status) {
        const statuses = {
            'PENDING': 'در انتظار',
            'AWAITING_APPROVAL': 'در انتظار تأیید پخش‌کننده',
            'CONFIRMED': 'تایید شده',
            'PROCESSING': 'در حال پردازش',
            'SHIPPED': 'ارسال شده',
            'DELIVERED': 'تحویل داده شده',
            'CANCELLED': 'لغو شده',
            'ACTIVE': 'فعال',
            'INACTIVE': 'غیرفعال',
            'PAID': 'پرداخت شده',
            'UNPAID': 'پرداخت نشده',
            'PARTIAL': 'نیمه‌تمام'
        };
        return statuses[status] || status;
    }

    getPaymentMethodLabel(method) {
        const methods = {
            'CASH': 'نقدی',
            'CARD': 'کارت به کارت',
            'ONLINE': 'آنلاین',
            'BALANCE': 'مانده حساب',
            'CHECK': 'پرداخت چکی',
            'WALLET': 'از مانده حساب',
            'CHEQUE': 'چک'
        };
        return methods[method] || method || 'نامشخص';
    }

    formatPrice(price) {
        if (!price && price !== 0) return '۰ تومان';
        return new Intl.NumberFormat('fa-IR').format(price) + ' تومان';
    }

    orderOutstanding(order) {
        const remaining = Number(order.remaining_amount);
        if (Number.isFinite(remaining)) return Math.max(remaining, 0);
        return Math.max(Number(order.total_price || 0) - Number(order.paid_amount || 0), 0);
    }

    // ========================================
    // تقویم شمسی برای فیلترهای تاریخ
    // ========================================
    jalaliEnhanceCust() {
        const toFaD = (v) => String(v == null ? '' : v).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[d]);
        let jCalFmt = null;
        try {
            jCalFmt = new Intl.DateTimeFormat('en-US-u-ca-persian', { year: 'numeric', month: 'numeric', day: 'numeric', timeZone: 'UTC' });
        } catch (e) { jCalFmt = null; }
        const jDateParts = (d) => {
            if (!jCalFmt) return [d.getFullYear(), d.getMonth() + 1, d.getDate()];
            const p = {};
            jCalFmt.formatToParts(d).forEach((x) => {
                if (x.type === 'year' || x.type === 'month' || x.type === 'day') p[x.type] = Number(x.value);
            });
            return [p.year, p.month, p.day];
        };
        const jMonths = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
        const jMonthTitle = (jy, jm) => toFaD(jy) + ' ' + (jMonths[jm - 1] || '');
        const gregOfJalali = (jy, jm) => {
            let g = new Date(Date.UTC(jy + 621, 2, 20));
            let cur;
            for (let iter = 0; iter < 6; iter++) {
                cur = jDateParts(g);
                if (cur[0] < jy || (cur[0] === jy && cur[1] < jm)) {
                    const monthsAhead = (jy - cur[0]) * 12 + (jm - cur[1]);
                    if (monthsAhead > 1) {
                        g = new Date(g.getTime() + Math.round(monthsAhead * 30.44) * 86400000);
                        continue;
                    }
                    let guard1 = 0;
                    while ((cur[0] < jy || (cur[0] === jy && cur[1] < jm)) && guard1++ < 400) {
                        g = new Date(g.getTime() + 86400000);
                        cur = jDateParts(g);
                    }
                }
                let guard2 = 0;
                while ((cur[0] > jy || (cur[0] === jy && cur[1] > jm)) && guard2++ < 400) {
                    g = new Date(g.getTime() - 86400000);
                    cur = jDateParts(g);
                }
                break;
            }
            cur = jDateParts(g);
            let guard3 = 0;
            while (cur[2] !== 1 && guard3++ < 40) {
                g = new Date(g.getTime() - 86400000);
                cur = jDateParts(g);
            }
            return g;
        };
        const jMonthLen = (jy, jm) => {
            if (jm <= 6) return 31;
            const ny = jm === 12 ? jy + 1 : jy;
            const nm = jm === 12 ? 1 : jm + 1;
            return Math.round((gregOfJalali(ny, nm).getTime() - gregOfJalali(jy, jm).getTime()) / 86400000);
        };
        document.querySelectorAll('input[type="date"]').forEach((inp) => {
            if (inp.closest('.jdate-wrap')) return;
            const wrap = document.createElement('div');
            wrap.className = 'jdate-wrap';
            inp.parentNode.insertBefore(wrap, inp.nextSibling);
            wrap.appendChild(inp);
            inp.style.display = 'none';
            const show = document.createElement('input');
            show.type = 'text';
            show.className = 'jdate-input';
            show.readOnly = true;
            show.placeholder = 'انتخاب تاریخ شمسی';
            const calIcon = document.createElement('span');
            calIcon.className = 'jcal-icon';
            calIcon.textContent = '📅';
            const pop = document.createElement('div');
            pop.className = 'jcal-pop';
            wrap.appendChild(show);
            wrap.appendChild(calIcon);
            wrap.appendChild(pop);
            const todayJ = jDateParts(new Date());
            const state = { jy: todayJ[0], jm: todayJ[1], open: false };
            const syncDisplay = () => {
                const m = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
                if (m) {
                    const j = jDateParts(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))));
                    show.value = jMonthTitle(j[0], j[1]) + ' ' + toFaD(j[2]);
                } else {
                    show.value = '';
                }
            };
            const close = () => { state.open = false; pop.classList.remove('open'); };
            const build = () => {
                const len = jMonthLen(state.jy, state.jm);
                const firstG = gregOfJalali(state.jy, state.jm);
                const firstCol = (firstG.getUTCDay() + 1) % 7;
                const cols = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
                let cell = '';
                for (let i = 0; i < firstCol; i++) cell += '<span></span>';
                for (let d = 1; d <= len; d++) {
                    const isToday = d === todayJ[2] && state.jy === todayJ[0] && state.jm === todayJ[1];
                    cell += '<span class="jcal-day' + (isToday ? ' today' : '') + '" data-d="' + d + '">' + toFaD(d) + '</span>';
                }
                pop.innerHTML = '<div class="jcal-nav"><button type="button" class="jcal-prev">‹</button><span class="jcal-title">' + jMonthTitle(state.jy, state.jm) + '</span><button type="button" class="jcal-next">›</button></div>'
                    + '<div class="jcal-grid">' + cols.map((c) => '<span class="jcal-head">' + c + '</span>').join('') + cell + '</div>';
            };
            wrap.addEventListener('click', (e) => {
                const navBtn = e.target.closest('.jcal-prev, .jcal-next');
                const day = e.target.closest('.jcal-day');
                if (state.open && navBtn) {
                    if (navBtn.classList.contains('jcal-prev')) {
                        state.jm--;
                        if (state.jm < 1) { state.jm = 12; state.jy--; }
                    } else {
                        state.jm++;
                        if (state.jm > 12) { state.jm = 1; state.jy++; }
                    }
                    build();
                    e.stopPropagation();
                    return;
                }
                if (state.open && day) {
                    const dd = Number(day.dataset.d);
                    const base = gregOfJalali(state.jy, state.jm);
                    const sel = new Date(base.getTime() + (dd - 1) * 86400000);
                    inp.value = sel.toISOString().slice(0, 10);
                    syncDisplay();
                    close();
                    inp.dispatchEvent(new Event('change', { bubbles: true }));
                    e.stopPropagation();
                    return;
                }
                if (state.open) { close(); e.stopPropagation(); return; }
                const curM = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
                if (curM) {
                    const cj = jDateParts(new Date(Date.UTC(Number(curM[1]), Number(curM[2]) - 1, Number(curM[3]))));
                    state.jy = cj[0];
                    state.jm = cj[1];
                } else {
                    state.jy = todayJ[0];
                    state.jm = todayJ[1];
                }
                build();
                state.open = true;
                pop.classList.add('open');
                e.stopPropagation();
            });
            syncDisplay();
        });
        document.addEventListener('click', () => {
            document.querySelectorAll('.jcal-pop.open').forEach((pop) => pop.classList.remove('open'));
        });
        window.jalaliSyncCust = () => {
            document.querySelectorAll('.jdate-wrap input[type="date"]').forEach((inp) => {
                const show = inp.parentNode.querySelector('.jdate-input');
                if (!show) return;
                const m = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
                if (m) {
                    const j = jDateParts(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))));
                    show.value = jMonthTitle(j[0], j[1]) + ' ' + toFaD(j[2]);
                } else {
                    show.value = '';
                }
            });
        };
    }

    chequeMediaUrl(path) {
        if (!path) return '';
        if (/^https?:\/\//.test(path)) return path;
        let base = '';
        try {
            base = (typeof API_URL === 'string' ? API_URL : '').replace(/\/api\/?$/, '');
        } catch (e) { /* noop */ }
        return base + (path.startsWith('/') ? path : '/' + path);
    }

    formatDate(dateString) {
        if (!dateString) return '---';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fa-IR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        } catch {
            return dateString;
        }
    }

    parsePersianDate(dateStr) {
        const parts = dateStr.split('/');
        if (parts.length !== 3) return null;
        try {
            const year = parseInt(parts[0]) + 621;
            const month = parseInt(parts[1]) - 1;
            const day = parseInt(parts[2]);
            return new Date(year, month, day);
        } catch {
            return null;
        }
    }

    hideLoader() {
        const loader = document.querySelector('.loader-overlay');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.display = 'none';
            }, 300);
        }
    }

    showToast(message, type = 'info') {
        if (typeof showAlert === 'function') {
            showAlert(message, type);
        } else {
            alert(message);
        }
    }
}

// ========================================
// راه‌اندازی خودکار داشبورد
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Dashboard Auto-Init Started...');
    
    const token = getAccessToken();
    console.log('🔑 Token:', token ? '✅ موجود' : '❌ وجود ندارد');
    
    if (!token) {
        console.warn('⛔ No token, redirecting to login...');
        window.location.href = 'log.html';
        return;
    }

    try {
        window.dashboard = new Dashboard();
        console.log('✅ Dashboard initialized successfully!');
        
        // ========================================
        // رویداد دکمه "همه خوانده شد"
        // ========================================
        const markAllReadBtn = document.getElementById('markAllReadBtn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', async function() {
                if (window.dashboard) {
                    await window.dashboard.markAllNotificationsAsRead();
                }
            });
        }
        
    } catch (error) {
        console.error('❌ Dashboard init error:', error);
    }
});

// ========================================
// نمایش جزئیات تیکت
// ========================================
function openTicketDetail(ticket) {
    const detail = document.getElementById('ticketDetail');
    const title = document.getElementById('detailTitle');
    const messages = document.getElementById('detailMessages');
    const replyInput = document.getElementById('replyInput');
    const sendReplyBtn = document.getElementById('sendReplyBtn');

    if (!detail || !title || !messages) return;

    const categoryLabels = {
        'GENERAL': 'عمومی',
        'ORDER': 'مشکل سفارش',
        'PRODUCT': 'سوال درباره محصول',
        'DELIVERY': 'مشکل ارسال',
        'PAYMENT': 'مشکل پرداخت',
        'TECHNICAL': 'مشکل فنی',
        'SUGGESTION': 'پیشنهاد',
        'COMPLAINT': 'شکایت'
    };

    const statusLabels = {
        'OPEN': 'باز',
        'ANSWERED': 'پاسخ داده شده',
        'CLOSED': 'بسته شده'
    };

    title.innerHTML = `
        <i class="fas fa-ticket-alt"></i> ${ticket.title}
        <span style="font-size:12px;font-weight:400;color:var(--text-gray);margin-right:12px;">
            ${categoryLabels[ticket.category] || ticket.category} | 
            وضعیت: ${statusLabels[ticket.status] || ticket.status}
        </span>
    `;

    const fmt = (d) => window.dashboard ? window.dashboard.formatDate(d) : d;
    const esc = (text) => String(text === null || text === undefined ? '' : text)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

    const items = [];

    const mediaHost = () => {
        let base = '';
        try {
            base = (typeof API_URL === 'string' ? API_URL : '').replace(/\/api\/?$/, '');
        } catch (e) { /* noop */ }
        return base;
    };
    const attachmentBlock = (att) => {
        if (!att || !att.url) return '';
        const full = /^https?:\/\//.test(att.url) ? att.url : mediaHost() + (att.url.startsWith('/') ? att.url : '/' + att.url);
        const isImage = /\.(png|jpe?g|gif|webp|bmp|svg|heic|avif|jpg)$/i.test(att.name || '');
        const link = `<div class="ticket-attach"><a href="${esc(full)}" target="_blank" rel="noopener"><i class="fas ${isImage ? 'fa-image' : 'fa-paperclip'}"></i> ${esc(att.name || 'پیوست')}</a></div>`;
        if (!isImage) return link;
        return `<div class="ticket-attach-img"><a href="${esc(full)}" target="_blank" rel="noopener"><img src="${esc(full)}" alt="${esc(att.name || '')}" /></a></div>`;
    };

    if (Array.isArray(ticket.messages) && ticket.messages.length > 0) {
        ticket.messages.forEach(msg => {
            const isStaff = msg.sender === 'STAFF';
            items.push({
                type: isStaff ? 'admin' : 'user',
                name: msg.sender_name || (isStaff ? 'پشتیبانی' : (ticket.user_name || 'شما')),
                text: msg.text || '',
                attaches: Array.isArray(msg.attachments) ? msg.attachments.map(attachmentBlock).join('') : '',
                time: fmt(msg.created_at)
            });
        });
    } else {
        items.push({
            type: 'user',
            name: ticket.user_name || 'شما',
            text: ticket.message,
            attaches: '',
            time: fmt(ticket.created_at)
        });
        if (ticket.admin_reply) {
            items.push({ type: 'admin', name: 'پشتیبانی', text: ticket.admin_reply, attaches: '', time: fmt(ticket.admin_replied_at) });
        }
        if (ticket.customer_reply) {
            items.push({ type: 'user', name: ticket.user_name || 'شما', text: ticket.customer_reply, attaches: '', time: fmt(ticket.customer_replied_at) });
        }
    }

    messages.innerHTML = items.map(m => `
        <div class="ticket-msg ${m.type}">
            <strong>${esc(m.name)}</strong><br>
            ${esc(m.text).replace(/\n/g, '<br>')}
            ${m.attaches}
            <div class="msg-meta">
                <span>${m.time}</span>
            </div>
        </div>
    `).join('') || '<div style="text-align:center;color:var(--text-gray);padding:20px;">هیچ پیامی وجود ندارد</div>';

    messages.scrollTop = messages.scrollHeight;

    detail.classList.add('active');

    sendReplyBtn.onclick = async function() {
        const reply = replyInput.value.trim();
        if (!reply) {
            showAlert('⚠️ لطفاً متن پاسخ را وارد کنید', 'error');
            return;
        }

        const response = await apiPost(`tickets/${ticket.id}/reply/`, {
            reply_message: reply
        });

        if (response.success) {
            showAlert('✅ پاسخ شما ارسال شد', 'success');
            replyInput.value = '';
            if (window.dashboard) {
                await window.dashboard.loadTickets();
                window.dashboard.renderTickets();
                const updatedTicket = window.dashboard.tickets.find(t => t.id === ticket.id);
                if (updatedTicket) {
                    openTicketDetail(updatedTicket);
                }
            }
        } else {
            showAlert('❌ خطا در ارسال پاسخ', 'error');
        }
    };

    detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
}