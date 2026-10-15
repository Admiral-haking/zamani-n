// ========================================
// ZAMANI - Secretary Panel (پنل منشی)
// ========================================

class SecretaryPanel {
    constructor() {
        this.dashboardData = null;
        this.customers = [];
        this.orders = [];
        this.tickets = [];
        this.products = [];
        this.distributors = [];
        this.transactions = [];
        this.checks = [];
        this._checksPage = 1;
        this._checksQuery = '';
        this.inventory = [];
        this.notifications = [];
        this._replyFiles = [];

        this.init();
    }

    // ========================================
    // INIT
    // ========================================

    async init() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = 'log.html';
            return;
        }

        await this.loadAllData();
        this.setupEventListeners();
    }

    // ========================================
    // LOAD ALL DATA
    // ========================================

    async loadAllData() {
        try {
            await Promise.all([
                this.loadDashboard(),
                this.loadCustomers(),
                this.loadOrders(),
                this.loadTickets(),
                this.loadProducts(),
                this.loadDistributors(),
                this.loadTransactions(),
                this.loadChecks(),
                this.loadInventory(),
                this.loadNotifications()
            ]);

            this.renderAll();
            console.log('✅ تمام داده‌ها بارگذاری شدند');
        } catch (error) {
            console.error('❌ خطا در بارگذاری داده‌ها:', error);
            this.showError('خطا در بارگذاری داده‌ها. لطفاً صفحه را مجدداً بارگذاری کنید.');
        }
    }

    // ========================================
    // LOAD: DASHBOARD
    // ========================================

    async loadDashboard(opts) {
        try {
            const o = opts || {};
            let endpoint = 'dashboard/';
            if (o.chart_period) {
                endpoint += '?chart_period=' + encodeURIComponent(o.chart_period);
            }
            const response = await apiGet(endpoint);
            if (response.success) {
                this.dashboardData = response.data;
            } else {
                console.error('خطا در دریافت داشبورد:', response.data);
            }
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    // ========================================
    // LOAD: CUSTOMERS
    // ========================================

    async loadCustomers() {
        try {
            const response = await apiGet('customers/');
            if (response.success) {
                this.customers = Array.isArray(response.data.results) ? response.data.results :
                               Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت مشتریان:', response.data);
            }
        } catch (error) {
            console.error('Error loading customers:', error);
        }
    }

    // ========================================
    // LOAD: ORDERS
    // ========================================

    async loadOrders() {
        try {
            const response = await apiGet('orders/');
            if (response.success) {
                this.orders = Array.isArray(response.data.results) ? response.data.results :
                            Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت سفارشات:', response.data);
            }
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }

    // ========================================
    // LOAD: TICKETS
    // ========================================

    async loadTickets() {
        try {
            const response = await apiGet('tickets/');
            if (response.success) {
                this.tickets = Array.isArray(response.data.results) ? response.data.results :
                             Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت تیکت‌ها:', response.data);
            }
        } catch (error) {
            console.error('Error loading tickets:', error);
        }
    }

    // ========================================
    // LOAD: PRODUCTS
    // ========================================

    async loadProducts() {
        try {
            const response = await apiGet('products/');
            if (response.success) {
                this.products = Array.isArray(response.data.results) ? response.data.results :
                               Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت محصولات:', response.data);
                this.products = [];
            }
        } catch (error) {
            console.error('Error loading products:', error);
            this.products = [];
        }
    }

    // ========================================
    // LOAD: DISTRIBUTORS
    // ========================================

    async loadDistributors() {
        try {
            const response = await apiGet('distributors/?page_size=100');
            if (response.success) {
                this.distributors = Array.isArray(response.data.results) ? response.data.results :
                                   Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت توزیع‌کنندگان:', response.data);
            }
        } catch (error) {
            console.error('Error loading distributors:', error);
        }
    }

    // ========================================
    // LOAD: TRANSACTIONS
    // ========================================

    async loadTransactions() {
        try {
            const response = await apiGet('finance/transactions/');
            if (response.success) {
                this.transactions = Array.isArray(response.data.results) ? response.data.results :
                                   Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت تراکنش‌ها:', response.data);
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
        }
    }

    // ========================================
    // LOAD: CHECKS
    // ========================================

    async loadChecks() {
        try {
            const response = await apiGet('finance/checks/');
            if (response.success) {
                this.checks = Array.isArray(response.data.results) ? response.data.results :
                             Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت چک‌ها:', response.data);
            }
        } catch (error) {
            console.error('Error loading checks:', error);
        }
    }

    // ========================================
    // LOAD: INVENTORY
    // ========================================

    async loadInventory() {
        try {
            const response = await apiGet('inventory/');
            if (response.success) {
                this.inventory = Array.isArray(response.data.results) ? response.data.results :
                                Array.isArray(response.data) ? response.data : [];
            } else {
                console.error('خطا در دریافت موجودی:', response.data);
            }
        } catch (error) {
            console.error('Error loading inventory:', error);
        }
    }

    // ========================================
    // LOAD: NOTIFICATIONS
    // ========================================

    async loadNotifications() {
        try {
            const response = await apiGet('notifications/');
            if (response.success) {
                this.notifications = Array.isArray(response.data.results) ? response.data.results :
                                    Array.isArray(response.data) ? response.data : [];
                this.updateNotificationBadge();
            } else {
                console.error('خطا در دریافت اعلانات:', response.data);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    // ========================================
    // RENDER ALL
    // ========================================

    renderAll() {
        this.renderDashboard();
        this.renderCustomers();
        this.renderOrders();
        this.renderTickets();
        this.renderRequests();
        this.renderProducts();
        this.renderDistributors();
        this.renderTransactions();
        this.renderChecks();
        this.renderInventory();
        this.renderNotifications();
        this.renderDashboardDetails();
        this.updateHeaderStats();
    }

    // ========================================
    // RENDER: DASHBOARD
    // ========================================

    renderDashboard() {
        if (!this.dashboardData) return;

        const data = this.dashboardData;

        this.updateElement('cardNewCustomers .value', data.today?.new_customers || 0);
        this.updateElement('cardOrdersToday .value', data.today?.orders_count || 0);
        this.updateElement('cardIncomeToday .value', this.formatPrice(data.today?.income || 0));
        this.updateElement('balanceValue', this.formatPrice(data.summary?.total_balance || 0));

        if (data.sales_chart && Array.isArray(data.sales_chart)) {
            this.renderSalesChart(data.sales_chart);
        }

        if (data.recent_tickets && Array.isArray(data.recent_tickets)) {
            this.renderRecentTickets(data.recent_tickets);
        }

        if (data.recent_orders && Array.isArray(data.recent_orders)) {
            this.renderRecentNotifications(data.recent_orders);
        }
    }

    renderSalesChart(chartData) {
        const chart = document.getElementById('salesChart');
        if (!chart || !Array.isArray(chartData) || chartData.length === 0) return;

        const maxValue = Math.max(...chartData.map(d => Number(d.total || 0)), 1);
        const barArea = Math.max((chart.clientHeight || 200) - 38, 60);

        chart.innerHTML = chartData.map(item => {
            const val = Number(item.total || 0);
            const heightPx = Math.max(4, Math.round(val / maxValue * barArea));
            const price = this.formatPrice(val);
            const label = item.label || item.day_name || '';
            const dayName = this.formatChartLabel(label);
            return `
                <div class="bar-item">
                    <div class="bar" style="height:${heightPx}px;"></div>
                    <div class="bar-value">${price}</div>
                    <div class="bar-label">${dayName}</div>
                </div>
            `;
        }).join('');
    }

    formatChartLabel(label) {
        if (!label) return '-';
        if (/^\d{4}-\d{2}-\d{2}$/.test(label)) {
            const p = label.split('-');
            return new Date(+p[0], +p[1] - 1, +p[2]).toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
        }
        if (/^\d{4}-\d{2}$/.test(label)) {
            const p = label.split('-');
            return new Date(+p[0], +p[1] - 1, 1).toLocaleDateString('fa-IR', { year: 'numeric', month: 'short' });
        }
        if (/^\d{4}$/.test(label)) {
            return new Date(+label, 0, 1).toLocaleDateString('fa-IR', { year: 'numeric' });
        }
        return String(label);
    }

    // ========================================
    // DASHBOARD: جزئیات باکس‌ها (امروز/درآمد/تراکنش‌ها)
    // ========================================

    _periodRange(period) {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        let from;
        if (period === 'weekly') {
            const day = (today.getDay() === 0) ? 6 : today.getDay() - 1;
            from = new Date(today);
            from.setDate(today.getDate() - day);
        } else if (period === 'monthly') {
            from = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (period === 'yearly') {
            from = new Date(today.getFullYear(), 0, 1);
        } else {
            from = today;
        }
        const to = today;
        return {
            from: from.getFullYear() + '-' + String(from.getMonth() + 1).padStart(2, '0') + '-' + String(from.getDate()).padStart(2, '0'),
            to: to.getFullYear() + '-' + String(to.getMonth() + 1).padStart(2, '0') + '-' + String(to.getDate()).padStart(2, '0')
        };
    }

    _orderInvoiceNumber(order) {
        return (order && order.tracking_code) ? String(order.tracking_code) : (order && order.id ? ('#' + order.id) : '—');
    }

    _statusBadgeHtml(status, label) {
        const cls = this.getOrderStatusClass ? this.getOrderStatusClass(status) : (status === 'CANCELLED' ? 'canceled' : '');
        const lbl = (this.getOrderStatusLabel ? this.getOrderStatusLabel(status) : status) || label || status || '—';
        return '<span class="status-badge ' + cls + '">' + lbl + '</span>';
    }

    _orderItemsHtml(order) {
        const items = Array.isArray(order.items) ? order.items : [];
        if (!items.length) return '—';
        return items
            .map(it => it.product_name || (it.name && it.name) || ('#' + (it.product || it.id)))
            .filter(Boolean)
            .join('، ');
    }

    _ordersTodayRowHtml(order) {
        const printBtn = '<button class="btn-secondary btn-sm print-invoice-btn" data-id="' + order.id + '" title="چاپ فاکتور"><i class="fas fa-print"></i> چاپ</button>';
        const method = this.getPaymentMethodLabel ? this.getPaymentMethodLabel(order.payment_method) : (order.payment_method || '---');
        return '<tr>'
            + '<td><span dir="ltr" style="display:inline-block;">' + this._orderInvoiceNumber(order) + '</span></td>'
            + '<td>' + (this.formatDate ? this.formatDate(order.created_at) : (order.created_at || '—')) + '</td>'
            + '<td>' + this._orderItemsHtml(order) + '</td>'
            + '<td>' + this.formatPrice(order.total_price) + '</td>'
            + '<td>' + this.formatPrice(order.paid_amount || 0) + '</td>'
            + '<td>' + this.formatPrice(order.balance || 0) + '</td>'
            + '<td>' + method + '</td>'
            + '<td>' + this._statusBadgeHtml(order.status) + '</td>'
            + '<td>' + printBtn + '</td>'
            + '</tr>';
    }

    _balanceRowHtml(order, index) {
        const printBtn = '<button class="btn-secondary btn-sm print-invoice-btn" data-id="' + order.id + '" title="چاپ فاکتور"><i class="fas fa-print"></i> چاپ</button>';
        const method = this.getPaymentMethodLabel ? this.getPaymentMethodLabel(order.payment_method) : (order.payment_method || '---');
        return '<tr>'
            + '<td>' + (index + 1) + '</td>'
            + '<td><span dir="ltr" style="display:inline-block;">' + this._orderInvoiceNumber(order) + '</span></td>'
            + '<td>' + (this.formatDate ? this.formatDate(order.created_at) : (order.created_at || '—')) + '</td>'
            + '<td>' + (order.customer_name || 'نامشخص') + '</td>'
            + '<td>' + this._orderItemsHtml(order) + '</td>'
            + '<td>' + this.formatPrice(order.total_price) + '</td>'
            + '<td>' + this.formatPrice(order.paid_amount || 0) + '</td>'
            + '<td>' + this.formatPrice(order.balance || 0) + '</td>'
            + '<td>' + method + '</td>'
            + '<td>' + this._statusBadgeHtml(order.status) + '</td>'
            + '<td>' + printBtn + '</td>'
            + '</tr>';
    }

    renderDashboardDetails(kind) {
        // ===== مشتریان جدید امروز =====
        if (!kind || kind === 'newCustomers') {
            const body = document.getElementById('newCustomersTableBody');
            if (body) {
                const now = new Date();
                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                const list = Array.isArray(this.customers) ? this.customers.filter(c => {
                    const d = (c && c.created_at || '').toString().slice(0, 10);
                    return d === todayStr;
                }) : [];
                if (!list.length) {
                    body.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-gray);">مشتری جدیدی امروز ثبت نشده است.</td></tr>';
                } else {
                    body.innerHTML = list.map(c => '<tr>'
                        + '<td>' + (c.company_name || c.full_name || c.username || 'مشتری #' + c.id) + '</td>'
                        + '<td>' + (c.phone || '—') + '</td>'
                        + '<td>' + (c.state || '—') + '</td>'
                        + '<td>' + (c.city || '—') + '</td>'
                        + '<td>' + (c.address || '—') + '</td>'
                        + '<td>' + (this.formatDate ? this.formatDate(c.created_at) : '—') + '</td>'
                        + '</tr>').join('');
                }
            }
        }

        // ===== سفارشات امروز =====
        if (!kind || kind === 'ordersToday') {
            const body = document.getElementById('ordersTodayTableBody');
            if (body) {
                const now = new Date();
                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                const list = Array.isArray(this.orders) ? this.orders.filter(o => (o.created_at || '').toString().slice(0, 10) === todayStr) : [];
                if (!list.length) {
                    body.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:var(--text-gray);">سفارشی امروز ثبت نشده است.</td></tr>';
                } else {
                    body.innerHTML = list.map(o => this._ordersTodayRowHtml(o)).join('');
                }
            }
        }

        // ===== جزئیات مانده حساب (آخرین فاکتورها) =====
        if (!kind || kind === 'balance') {
            const body = document.getElementById('balanceDetailBody');
            if (body) {
                const list = Array.isArray(this.orders) ? this.orders.slice(0, 25) : [];
                if (!list.length) {
                    body.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:20px;color:var(--text-gray);">فاکتوری ثبت نشده است.</td></tr>';
                } else {
                    body.innerHTML = list.map((o, i) => this._balanceRowHtml(o, i)).join('');
                }
            }
        }

        // ===== لیست درآمد (بر اساس بازه انتخابی) =====
        if (!kind || kind === 'income') {
            const body = document.getElementById('incomeTableBody');
            if (body) {
                const period = this._detailPeriods && this._detailPeriods.income ? this._detailPeriods.income : 'daily';
                const range = this._periodRange(period);
                const list = Array.isArray(this.orders) ? this.orders.filter(o => {
                    const d = (o.created_at || '').toString().slice(0, 10);
                    return d >= range.from && d <= range.to && o.status !== 'CANCELLED' && o.status !== 'PENDING';
                }) : [];
                if (!list.length) {
                    body.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--text-gray);">درآمدی در این بازه ثبت نشده است.</td></tr>';
                } else {
                    body.innerHTML = list.map(o => '<tr>'
                        + '<td>' + (o.customer_name || 'نامشخص') + '</td>'
                        + '<td>' + this.formatPrice(o.total_price) + '</td>'
                        + '<td><span dir="ltr">' + this._orderInvoiceNumber(o) + '</span></td>'
                        + '<td>' + this._statusBadgeHtml(o.status) + '</td>'
                        + '</tr>').join('');
                }
            }
        }
    }

    async setChartPeriod(period) {
        this._chartPeriod = period;
        await this.loadDashboard({ chart_period: period });
        this.renderDashboard();
        this.renderDashboardDetails();
    }

    setDetailPeriod(kind, period) {
        if (!this._detailPeriods) this._detailPeriods = {};
        this._detailPeriods[kind] = period;
        this.renderDashboardDetails(kind);
    }

    renderRecentTickets(tickets) {
        const container = document.getElementById('dashboardTickets');
        if (!container) return;

        if (!Array.isArray(tickets) || tickets.length === 0) {
            container.innerHTML = `
                <div class="ticket-item" style="justify-content:center;color:var(--text-gray);">
                    <span>هیچ تیکت باز و نیازمند پاسخی وجود ندارد.</span>
                </div>
            `;
            return;
        }

        container.innerHTML = tickets.map(ticket => `
            <div class="ticket-item" data-ticket="${ticket.id}">
                <div class="ticket-info">
                    <div class="ticket-title"><i class="fas fa-tag"></i> ${ticket.title}</div>
                    <div class="ticket-meta">
                        <span><i class="fas fa-user"></i> ${ticket.user || 'کاربر'}</span>
                        <span><i class="fas fa-clock"></i> ${this.formatDate(ticket.created_at)}</span>
                        ${ticket.status === 'ANSWERED' ? '<span class="status-badge answered">پاسخ داده شده</span>' : '<span class="status-badge pending">پاسخ داده نشده</span>'}
                    </div>
                </div>
                <div class="ticket-actions">
                    <button class="btn-primary btn-sm answer-ticket" data-id="${ticket.id}">پاسخ</button>
                </div>
            </div>
        `).join('');
    }

    renderRecentNotifications(orders) {
        const container = document.querySelector('.notif-list');
        if (!container || !Array.isArray(orders)) return;

        const notifications = orders.slice(0, 3).map(order => `
            <div class="notif-item">
                <span class="notif-text"><i class="fas fa-box"></i> سفارش جدید #${order.id} - ${order.customer}</span>
                <span class="notif-time">${this.formatDate(order.created_at)}</span>
            </div>
        `).join('');

        if (notifications) {
            container.innerHTML = notifications + container.innerHTML;
        }
    }

    // ========================================
    // RENDER: CUSTOMERS
    // ========================================

    renderCustomers() {
        const container = document.getElementById('customerList');
        if (!container) return;
        if (container.dataset.inlineRendered === '1') return;

        if (!Array.isArray(this.customers) || this.customers.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-users" style="font-size:40px;display:block;margin-bottom:12px;"></i>
                    هیچ مشتری‌ای ثبت نشده است.
                </div>
            `;
            return;
        }

        container.innerHTML = this.customers.map(customer => `
            <div class="customer-card" data-customer="${customer.id}">
                <div class="customer-info">
                    <div class="name">${customer.company_name || customer.full_name || 'بدون نام'}</div>
                    <div class="detail">
                        <span><i class="fas fa-phone"></i> ${customer.phone || 'نامشخص'}</span>
                        <span><i class="fas fa-shopping-cart"></i> ${customer.total_orders || 0} سفارش</span>
                        <span><i class="fas fa-star"></i> ${customer.points || 0} امتیاز</span>
                        <span><i class="fas fa-id-card"></i> ${customer.customer_code || '---'}</span>
                    </div>
                </div>
                <div class="customer-badges">
                    ${customer.is_active ? '<span class="tag vip">فعال</span>' : '<span class="tag complaint">غیرفعال</span>'}
                    ${customer.account_balance > 0 ? `<span class="tag wholesale">${this.formatPrice(customer.account_balance)}</span>` : ''}
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                    <button class="btn-primary btn-sm view-customer" data-id="${customer.id}">پروفایل</button>
                    <button class="btn-secondary btn-sm msg-customer" data-id="${customer.id}">پیام</button>
                </div>
            </div>
        `).join('');
    }

    // ========================================
    // RENDER: ORDERS
    // ========================================

    renderOrders() {
        const container = document.getElementById('invoiceTableBody');
        if (!container) return;

        if (!Array.isArray(this.orders) || this.orders.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="11" style="text-align:center;padding:30px;color:var(--text-gray);">
                        هیچ سفارشی وجود ندارد.
                    </td>
                </tr>
            `;
            return;
        }

        container.innerHTML = this.orders.slice(0, 20).map(order => `
            <tr data-status="${order.status || 'pending'}">
                <td>#${order.id}</td>
                <td>${order.customer_name || 'نامشخص'}</td>
                <td>${this.formatDate(order.created_at)}</td>
                <td>${this.formatPrice(order.total_price)}</td>
                <td>${this.formatPrice(order.paid_amount || 0)}</td>
                <td class="${order.balance && order.balance > 0 ? 'tx-amount minus' : ''}">${this.formatPrice(order.balance || 0)}</td>
                <td>${this.getPaymentMethodLabel(order.payment_method)}</td>
                <td><span class="status-badge ${this.getOrderStatusClass(order.status)}">${this.getOrderStatusLabel(order.status)}</span></td>
                <td>
                    <button class="btn-secondary btn-sm view-order" data-id="${order.id}">مشاهده</button>
                </td>
                <td>
                    ${this.getOrderReceipts(order).length ? `<button class="btn-secondary btn-sm view-receipt" data-order="${order.id}"><i class="fas fa-paperclip"></i> رسید</button>` : ''}
                </td>
                <td>
                    ${order.status === 'PENDING' ? `
                        <button class="btn-success btn-sm approve-invoice" data-id="${order.id}"><i class="fas fa-check"></i></button>
                        <button class="btn-danger btn-sm reject-invoice" data-id="${order.id}"><i class="fas fa-times"></i></button>
                    ` : ''}
                    <button class="btn-secondary btn-sm print-invoice-btn" data-id="${order.id}" title="چاپ فاکتور"><i class="fas fa-print"></i></button>
                </td>
            </tr>
        `).join('');
    }

    // ========================================
    // PRINT: چاپ فاکتور (سبک حسابداری)
    // ========================================

    async printOrderInvoice(order) {
        if (!order) return;

        let full = order;
        if (!Array.isArray(order.items) || !order.items.length) {
            try {
                const res = await apiGet(`orders/${order.id}/`);
                if (res && res.success && res.data) full = res.data;
            } catch (e) { /* noop */ }
        }

        const fa = (n) => {
            if (n === null || n === undefined || isNaN(Number(n))) return '۰';
            return Math.round(Number(n)).toLocaleString('fa-IR');
        };
        const fmt = (d) => this.formatDate ? this.formatDate(d) : (d || '—');

        const items = Array.isArray(full.items) ? full.items : [];
        const paid = full.paid_amount || 0;
        const total = full.total_price || 0;
        const remain = Math.max(total - paid, 0);

        const paymentLabels = {
            'ONLINE': 'آنلاین', 'CARD': 'کارت به کارت', 'CASH': 'نقدی',
            'CHEQUE': 'چکی', 'CHECK': 'چکی', 'BALANCE': 'از حساب', 'CREDIT': 'اعتباری'
        };
        const method = paymentLabels[full.payment_method] || full.payment_method || '---';

        const itemRows = items.length ? items.map((it, i) => {
            const name = (it && (it.product_name || it.name)) || 'محصول';
            const qty = parseInt(it.quantity) || 1;
            const price = Number(it.price) || 0;
            return '<tr>'
                + '<td style="text-align:center;">' + fa(i + 1) + '</td>'
                + '<td>' + name + '</td>'
                + '<td style="text-align:center;">' + fa(qty) + '</td>'
                + '<td>' + fa(price) + ' تومان</td>'
                + '<td>' + fa(it.discount || 0) + ' تومان</td>'
                + '<td>' + fa(price * qty) + ' تومان</td>'
                + '</tr>';
        }).join('') : '<tr><td colspan="6" style="text-align:center;color:#999;">—</td></tr>';

        const statusLabel = this.getOrderStatusLabel ? this.getOrderStatusLabel(full.status) : full.status;

        const html = `<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>فاکتور فروش #${full.id}</title>
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
            <div class="side" style="text-align:right;">شماره فاکتور: ${fa(full.id)}</div>
            <div class="doc-title">فاکتور فروش</div>
            <div class="side" style="text-align:left;">تاریخ: ${fmt(full.created_at)}</div>
        </div>
        <div class="meta">
            <div><b>نام مشتری:</b> ${full.customer_name || '—'}</div>
            <div><b>کد رهگیری:</b> ${full.tracking_code || '—'}</div>
            <div><b>روش پرداخت:</b> ${method}</div>
            <div><b>وضعیت:</b> ${statusLabel}</div>
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
            <tr><td>جمع کل:</td><td style="text-align:left;">${fa(total)} تومان</td></tr>
            <tr><td>تخفیف کل:</td><td style="text-align:left;">${fa(full.total_discount || 0)} تومان</td></tr>
            <tr><td>پرداخت شده:</td><td style="text-align:left;">${fa(paid)} تومان</td></tr>
            <tr><td class="final">مانده بدهی:</td><td class="final" style="text-align:left;">${fa(remain)} تومان</td></tr>
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

        const win = window.open('', '_blank', 'width=900,height=700');
        if (!win) {
            alert('لطفاً اجازه باز کردن پنجره چاپ را بدهید.');
            return;
        }
        win.document.open();
        win.document.write(html);
        win.document.close();
    }

    // ========================================
    // ORDER DETAIL MODAL (تایید فاکتور با جزئیات کامل خرید)
    // ========================================

    openOrderDetail(order) {
        let modal = document.getElementById('orderDetailModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.id = 'orderDetailModal';
            modal.innerHTML = `
                <div class="modal-box" style="max-width:660px;width:100%;">
                    <h3><i class="fas fa-file-invoice"></i> جزئیات فاکتور خرید</h3>
                    <div style="max-height:65vh;overflow-y:auto;padding:2px;" id="orderDetailBody"></div>
                    <div class="modal-actions" id="orderDetailActions"></div>
                </div>
            `;
            document.body.appendChild(modal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        }

        const methodLabels = this.getPaymentMethodLabel.bind(this);

        const items = Array.isArray(order.items) ? order.items : [];
        const itemsHtml = items.length ? items.map(it => {
            const qty = Number(it.quantity) || 0;
            const price = Number(it.price) || 0;
            return `
                <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                    <td style="padding:8px;text-align:right;">${it.product_name || ('محصول #' + it.product)}</td>
                    <td style="padding:8px;text-align:center;">${qty}</td>
                    <td style="padding:8px;text-align:center;">${this.formatPrice(price)}</td>
                    <td style="padding:8px;text-align:center;"><strong>${this.formatPrice(price * qty)}</strong></td>
                </tr>`;
        }).join('') : '<tr><td colspan="4" style="text-align:center;color:var(--text-gray);padding:14px;">آیتمی ثبت نشده است</td></tr>';

        const body = document.getElementById('orderDetailBody');
        body.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 18px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:16px;margin-bottom:14px;font-size:13px;">
                <div><span style="color:var(--text-gray);">شماره فاکتور:</span> <strong>#${order.id}</strong></div>
                <div><span style="color:var(--text-gray);">کد رهگیری:</span> <strong dir="ltr">${order.tracking_code || '—'}</strong></div>
                <div><span style="color:var(--text-gray);">مشتری:</span> <strong>${order.customer_name || 'نامشخص'}</strong></div>
                <div><span style="color:var(--text-gray);">تاریخ ثبت:</span> <strong>${this.formatDate(order.created_at)}</strong></div>
                <div><span style="color:var(--text-gray);">روش پرداخت:</span> <strong>${methodLabels(order.payment_method)}</strong></div>
                <div><span style="color:var(--text-gray);">وضعیت:</span> <span class="status-badge ${this.getOrderStatusClass(order.status)}">${this.getOrderStatusLabel(order.status)}</span></div>
            </div>
            <div style="font-size:13px;font-weight:bold;margin-bottom:8px;">📦 محصولات خریداری‌شده</div>
            <table style="width:100%;border-collapse:collapse;font-size:12.5px;margin-bottom:14px;">
                <thead>
                    <tr style="color:var(--text-gray);border-bottom:1px solid rgba(255,255,255,0.1);">
                        <th style="padding:8px;text-align:right;">نام محصول</th>
                        <th style="padding:8px;text-align:center;">تعداد</th>
                        <th style="padding:8px;text-align:center;">قیمت واحد</th>
                        <th style="padding:8px;text-align:center;">جمع</th>
                    </tr>
                </thead>
                <tbody>${itemsHtml}</tbody>
            </table>
            <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:13px;">
                <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:10px 14px;flex:1;min-width:130px;">مبلغ کل: <strong style="color:var(--mustard-yellow);">${this.formatPrice(order.total_price)}</strong></div>
                <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:10px 14px;flex:1;min-width:130px;">پرداخت شده: <strong style="color:#2ecc71;">${this.formatPrice(order.paid_amount || 0)}</strong></div>
                <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:10px 14px;flex:1;min-width:130px;">مانده بدهی: <strong style="color:#e74c3c;">${this.formatPrice(order.balance || 0)}</strong></div>
            </div>
            ${(() => {
                const receipts = this.getOrderReceipts(order);
                if (!receipts.length) return '';
                return `
                    <div style="font-size:13px;font-weight:bold;margin:14px 0 8px;"><i class="fas fa-paperclip"></i> رسید پرداخت</div>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;">
                        ${receipts.map(r => `
                            <button class="btn-secondary btn-sm view-receipt" data-order="${order.id}"><i class="fas fa-paperclip"></i> ${r.name || 'مشاهده رسید'}</button>
                        `).join('')}
                    </div>
                `;
            })()}
        `;

        let actionsHtml = '<button class="btn-secondary" id="closeOrderDetailModal">بستن</button><button class="btn-primary" id="printOrderFromDetail"><i class="fas fa-print"></i> چاپ فاکتور</button>';
        if (order.status === 'PENDING') {
            actionsHtml = '<button class="btn-primary" id="approveOrderFromDetail"><i class="fas fa-check"></i> تایید فاکتور</button>' + actionsHtml + '<button class="btn-danger" id="rejectOrderFromDetail"><i class="fas fa-times"></i> لغو فاکتور</button>';
        }
        document.getElementById('orderDetailActions').innerHTML = actionsHtml;

        document.getElementById('closeOrderDetailModal').addEventListener('click', () => {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        });
        const printBtn = document.getElementById('printOrderFromDetail');
        if (printBtn) {
            printBtn.addEventListener('click', () => { this.printOrderInvoice(order); });
        }
        const approveBtn = document.getElementById('approveOrderFromDetail');
        if (approveBtn) {
            approveBtn.addEventListener('click', async () => {
                const ok = await this.performConfirm(order.id);
                if (ok) { modal.classList.remove('active'); document.body.style.overflow = ''; }
            });
        }
        const rejectBtn = document.getElementById('rejectOrderFromDetail');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', async () => {
                const ok = await this.performCancel(order.id);
                if (ok) { modal.classList.remove('active'); document.body.style.overflow = ''; }
            });
        }

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    async performConfirm(id) {
        if (!confirm(`آیا از تایید فاکتور #${id} اطمینان دارید؟`)) return false;
        const response = await apiPost(`orders/${id}/confirm/`);
        if (response.success) {
            this.showSuccess(`فاکتور #${id} با موفقیت تایید شد و پرداخت آن تسویه گردید`);
            await this.refreshAfterOrderAction();
            return true;
        }
        this.showError('خطا در تایید فاکتور: ' + ((response.data && (response.data.detail || response.data.error)) || 'خطا'));
        return false;
    }

    async performCancel(id) {
        if (!confirm(`آیا از لغو فاکتور #${id} اطمینان دارید؟`)) return false;
        const response = await apiPost(`orders/${id}/cancel/`);
        if (response.success) {
            this.showSuccess(`فاکتور #${id} با موفقیت لغو شد`);
            await this.refreshAfterOrderAction();
            return true;
        }
        this.showError('خطا در لغو فاکتور');
        return false;
    }

    // به‌روزرسانی همزمان تمام بخش‌های پنل منشی (فاکتورها، مشتریان، گزارش مالی و داشبورد)
    async refreshAfterOrderAction() {
        try {
            if (typeof window.loadFinancialData === 'function') window.loadFinancialData();
        } catch (e) { /* noop */ }
        try {
            if (typeof window.loadCustomersData === 'function') window.loadCustomersData();
        } catch (e) { /* noop */ }
        try {
            await this.loadOrders();
            this.renderOrders();
        } catch (e) { /* noop */ }
        try {
            await this.loadTransactions();
            this.renderTransactions();
        } catch (e) { /* noop */ }
        try {
            await this.loadDashboard();
            this.renderDashboard();
            this.renderDashboardDetails();
        } catch (e) { /* noop */ }
    }

    getOrderReceipts(order) {
        const payments = Array.isArray(order && order.payments) ? order.payments : [];
        const seen = {};
        const result = [];
        payments.forEach(p => {
            if (p && p.receipt && !seen[p.receipt]) {
                seen[p.receipt] = true;
                result.push({ url: p.receipt, name: p.receipt_name || '', status: p.status, method: p.method });
            }
        });
        return result;
    }

    isImageUrl(url) {
        return /\.(png|jpe?g|gif|webp|bmp)$/i.test((url || '').split('?')[0]);
    }

    receiptBlockHtml(receipt) {
        const url = receipt.url;
        const name = receipt.name || 'رسید';
        const preview = this.isImageUrl(url)
            ? `<img src="${url}" alt="${name}" style="max-width:100%;max-height:320px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);display:block;margin:0 auto;">`
            : `<div style="padding:22px;text-align:center;color:var(--text-gray);border:1px dashed rgba(255,255,255,0.2);border-radius:10px;"><i class="fas fa-file-pdf" style="font-size:34px;display:block;margin-bottom:8px;color:#e74c3c;"></i>فایل PDF قابل دانلود است</div>`;
        const statusLabel = receipt.status === 'SUCCESS' ? 'تایید شده' : 'در انتظار تایید';
        return `
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:12px;margin-bottom:12px;">
                <div style="font-size:12.5px;color:var(--text-gray);margin-bottom:10px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;">
                    <span><i class="fas fa-paperclip"></i> ${name}</span>
                    <span class="status-badge ${receipt.status === 'SUCCESS' ? 'paid' : 'waiting'}">${statusLabel}</span>
                </div>
                ${preview}
                <div style="text-align:center;margin-top:10px;">
                    <a href="${url}" target="_blank" rel="noopener" class="btn-secondary btn-sm" download="${name}"><i class="fas fa-download"></i> دانلود فایل</a>
                </div>
            </div>
        `;
    }

    openReceiptModal(receipts) {
        if (!Array.isArray(receipts) || receipts.length === 0) {
            this.showError('رسیدی برای این سفارش ثبت نشده است.');
            return;
        }
        let modal = document.getElementById('receiptModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.id = 'receiptModal';
            modal.innerHTML = `
                <div class="modal-box" style="max-width:520px;width:100%;">
                    <h3><i class="fas fa-receipt"></i> رسید پرداخت</h3>
                    <div style="max-height:65vh;overflow-y:auto;padding:2px;" id="receiptModalBody"></div>
                    <div class="modal-actions"><button class="btn-secondary" id="closeReceiptModal">بستن</button></div>
                </div>
            `;
            document.body.appendChild(modal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        }
        document.getElementById('receiptModalBody').innerHTML = receipts.map(r => this.receiptBlockHtml(r)).join('');
        document.getElementById('closeReceiptModal').addEventListener('click', () => {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        });
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // ========================================
    // RENDER: TICKETS
    // ========================================

    renderTickets() {
        const container = document.getElementById('ticketList');
        if (!container) return;

        if (!Array.isArray(this.tickets) || this.tickets.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-gray);">
                    <i class="fas fa-ticket-alt" style="font-size:40px;display:block;margin-bottom:12px;"></i>
                    هیچ تیکتی وجود ندارد.
                </div>
            `;
            return;
        }

        const roleLabels = {
            'CUSTOMER': 'مشتری',
            'DISTRIBUTOR': 'توزیع‌کننده',
            'ADMIN': 'ادمین',
            'SECRETARY': 'منشی',
            'GUEST': 'مهمان'
        };

        container.innerHTML = this.tickets.map(ticket => {
            const senderName = ticket.user_name || ticket.user?.username || 'کاربر';
            const senderPhone = ticket.user_phone || ticket.guest_phone || '—';
            const senderCompany = ticket.user_company || '';
            const senderRole = roleLabels[ticket.user_role] || roleLabels[ticket.user?.role] || 'مشتری';
            const lastMsg = Array.isArray(ticket.messages) && ticket.messages.length
                ? ticket.messages[ticket.messages.length - 1].text
                : (ticket.message || '');
            return `
            <div class="ticket-item" data-ticket="${ticket.id}" data-status="${ticket.status}" data-sender="${ticket.user_role || ticket.user?.role || 'customer'}">
                <div class="ticket-info">
                    <div class="ticket-title"><i class="fas fa-tag"></i> ${ticket.title}</div>
                    <div class="ticket-meta">
                        <span title="فرستنده"><i class="fas fa-user"></i> ${senderName}</span>
                        ${senderCompany ? `<span title="نام شرکت"><i class="fas fa-building"></i> ${senderCompany}</span>` : ''}
                        <span title="تلفن"><i class="fas fa-phone"></i> ${senderPhone}</span>
                        <span class="status-badge pending" style="font-size:10px;">${senderRole}</span>
                        <span><i class="fas fa-calendar"></i> ${this.formatDate(ticket.created_at)}</span>
                        <span class="status-badge ${ticket.status === 'ANSWERED' ? 'answered' : 'pending'}">${ticket.status === 'ANSWERED' ? 'پاسخ داده شده' : 'پاسخ داده نشده'}</span>
                    </div>
                    <div style="font-size:12px;color:var(--text-gray);margin-top:4px;max-width:85%;">
                        ${lastMsg.length > 80 ? lastMsg.substring(0, 80) + '...' : lastMsg}
                    </div>
                </div>
                <div class="ticket-actions">
                    <button class="btn-secondary btn-sm view-ticket" data-id="${ticket.id}">مشاهده</button>
                    <button class="btn-primary btn-sm answer-ticket" data-id="${ticket.id}">پاسخ</button>
                    <button class="btn-secondary btn-sm note-ticket" data-id="${ticket.id}"><i class="fas fa-sticky-note"></i></button>
                </div>
            </div>`;
        }).join('');

        this.updateTicketBadge();
    }

    updateTicketBadge() {
        const openTickets = Array.isArray(this.tickets) ? this.tickets.filter(t => t.status !== 'CLOSED').length : 0;
        const badge = document.getElementById('ticketBadge');
        if (badge) {
            badge.textContent = openTickets;
            badge.style.display = openTickets > 0 ? '' : 'none';
        }
    }

    // ========================================
    // RENDER: REQUESTS (درخواست‌ها و شکایات)
    // ========================================

    renderRequests() {
        const tbody = document.getElementById('requestsTableBody');
        if (!tbody) return;

        const categoryLabels = {
            'COMPLAINT': 'شکایت',
            'ACCOUNT_REQUEST': 'درخواست حساب',
            'SUGGESTION': 'پیشنهاد'
        };
        const requestTypes = ['COMPLAINT', 'ACCOUNT_REQUEST', 'SUGGESTION'];
        const all = Array.isArray(this.tickets)
            ? this.tickets.filter(t => requestTypes.indexOf(t.category) !== -1)
            : [];

        const pageSize = 15;
        let currentPage = 1;
        const totalPages = Math.max(1, Math.ceil(all.length / pageSize));

        if (all.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--text-gray);">پیامی یافت نشد.</td></tr>`;
            const pagination = document.getElementById('requestsPagination');
            if (pagination) pagination.innerHTML = '';
            return;
        }

        const renderPage = () => {
            const start = (currentPage - 1) * pageSize;
            const end = Math.min(start + pageSize, all.length);
            const pageData = all.slice(start, end);

            tbody.innerHTML = pageData.map(ticket => {
                const statusText = ticket.status === 'ANSWERED' ? 'پاسخ داده شده' : ticket.status === 'CLOSED' ? 'بسته شده' : 'باز';
                const customer = ticket.user_name || ticket.user?.username || '—';
                return `<tr>
                    <td>${ticket.id}</td>
                    <td>${categoryLabels[ticket.category] || ticket.category}</td>
                    <td>${this.escapeHtml(customer)}</td>
                    <td>${this.formatDate(ticket.created_at)}</td>
                    <td><span class="status-badge ${ticket.status === 'ANSWERED' ? 'answered' : 'pending'}">${statusText}</span></td>
                    <td><button class="btn-danger btn-sm delete-request" data-id="${ticket.id}" title="حذف پیام"><i class="fas fa-trash"></i> حذف</button></td>
                </tr>`;
            }).join('');
        };

        const renderPagination = () => {
            const pagination = document.getElementById('requestsPagination');
            if (!pagination) return;
            let html = '';
            html += `<button class="prev-btn" ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">قبلی</button>`;
            for (let i = 1; i <= totalPages; i++) {
                html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
            }
            html += `<button class="next-btn" ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">بعدی</button>`;
            pagination.innerHTML = html;
        };

        renderPage();
        renderPagination();

        const pagination = document.getElementById('requestsPagination');
        if (pagination) {
            pagination.querySelectorAll('button[data-page]').forEach(btn => {
                btn.addEventListener('click', function() {
                    const page = Number(this.dataset.page);
                    if (page < 1 || page > totalPages) return;
                    currentPage = page;
                    renderPage();
                    renderPagination();
                    pagination.querySelectorAll('button[data-page]').forEach(b => {
                        b.replaceWith(b.cloneNode(true));
                    });
                });
            });
        }

        const tbodyPending = tbody;
        const self = this;
        Array.from(tbodyPending.querySelectorAll('.delete-request')).forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.dataset.id;
                if (!confirm('آیا از حذف این پیام مطمئن هستید؟')) return;
                const response = await apiDelete(`tickets/${id}/`);
                if (response && response.success) {
                    self.tickets = (self.tickets || []).filter(t => t.id != id);
                    self.renderRequests();
                    self.renderTickets();
                    self.updateTicketBadge();
                    self.showSuccess('پیام با موفقیت حذف شد.');
                } else {
                    self.showError((response && response.data && response.data.detail) || 'خطا در حذف پیام.');
                }
            });
        });
    }

    // ========================================
    // RENDER: PRODUCTS
    // ========================================

    renderProducts() {
        const container = document.querySelector('#section-products .data-table tbody');
        if (!container) return;

        if (!Array.isArray(this.products) || this.products.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center;padding:30px;color:var(--text-gray);">
                        هیچ محصولی وجود ندارد.
                    </td>
                </tr>
            `;
            return;
        }

        container.innerHTML = this.products.map(product => `
            <tr>
                <td>${product.name || 'بدون نام'}</td>
                <td>${this.formatPrice(product.base_price || 0)}</td>
                <td>${this.getProductStock(product.id) || 0}</td>
                <td><span class="status-badge ${product.is_active ? 'paid' : 'canceled'}">${product.is_active ? 'فعال' : 'غیرفعال'}</span></td>
                <td>
                    <button class="btn-secondary btn-sm edit-product" data-id="${product.id}">ویرایش</button>
                    <button class="btn-danger btn-sm delete-product" data-id="${product.id}">حذف</button>
                </td>
            </tr>
        `).join('');
    }

    getProductStock(productId) {
        if (!Array.isArray(this.inventory)) return 0;
        const inv = this.inventory.find(i => i.product === productId || i.product?.id === productId);
        return inv?.quantity || 0;
    }

    // ========================================
    // RENDER: DISTRIBUTORS
    // ========================================

    renderDistributors() {
        this.renderDistributorList(this.distributors);
    }

    renderDistributorList(list) {
        const container = document.getElementById('distributorTableBody');
        if (!container) return;
        if (container.dataset.inlineRendered === '1') return;

        if (!Array.isArray(list) || list.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center;padding:30px;color:var(--text-gray);">
                        هیچ توزیع‌کننده‌ای وجود ندارد.
                    </td>
                </tr>
            `;
            return;
        }

        const me = this;
        container.innerHTML = list.map(distributor => `
            <tr data-distributor="${distributor.id}">
                <td>${distributor.full_name}</td>
                <td>${distributor.city || '---'}</td>
                <td>${distributor.today_orders || 0}</td>
                <td>${distributor.shipping_orders || 0}</td>
                <td>
                    <button class="btn-secondary btn-sm view-distributor-purchases" data-id="${distributor.id}" data-name="${distributor.full_name || distributor.name || ''}" title="تاریخچه خریدها">تاریخچه</button>
                    <button class="btn-primary btn-sm distributor-ticket-btn" data-id="${distributor.id}" data-name="${distributor.full_name || distributor.name || ''}" title="تیکت">تیکت</button>
                    <button class="btn-secondary btn-sm edit-distributor" data-id="${distributor.id}" data-name="${distributor.full_name || distributor.name || ''}" data-city="${distributor.city || ''}" data-phone="${distributor.phone || ''}" title="ویرایش پخش‌کننده و قیمت محصولات">ویرایش</button>
                    <button class="btn-danger btn-sm delete-distributor" data-id="${distributor.id}" data-name="${distributor.full_name || distributor.name || ''}" title="حذف پخش‌کننده">حذف</button>
                </td>
            </tr>
        `).join('');

        container.querySelectorAll('.view-distributor-purchases').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                const name = this.dataset.name || '';
                if (typeof window.openDistributorPurchases === 'function') {
                    window.openDistributorPurchases(id, name);
                }
            });
        });

        container.querySelectorAll('.distributor-ticket-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                const name = this.dataset.name || '';
                if (typeof window.openDistributorTicket === 'function') {
                    window.openDistributorTicket(id, name);
                }
            });
        });

        container.querySelectorAll('.edit-distributor').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                const name = this.dataset.name || '';
                const nameEl = document.getElementById('newDistributorName');
                const userEl = document.getElementById('newDistributorUsername');
                const passEl = document.getElementById('newDistributorPassword');
                const cityEl = document.getElementById('newDistributorCity');
                const phoneEl = document.getElementById('newDistributorPhone');
                if (nameEl) nameEl.value = name;
                if (userEl) { userEl.value = ''; }
                if (passEl) { passEl.value = ''; }
                if (cityEl) cityEl.value = this.dataset.city || '';
                if (phoneEl) phoneEl.value = this.dataset.phone || '';
                if (typeof window.openDistributorPriceEditor === 'function') {
                    window.openDistributorPriceEditor(id, name);
                }
            });
        });

        container.querySelectorAll('.delete-distributor').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                const name = this.dataset.name || '';
                if (!confirm('آیا از حذف پخش‌کننده «' + name + '» مطمئن هستید؟')) return;
                apiDelete('distributors/' + id + '/').then(function(res) {
                    if (res && res.success) {
                        if (typeof window.showMsg === 'function') {
                            window.showMsg('addDistributorMsg', '✅ پخش‌کننده ' + name + ' حذف شد.', 'success');
                        } else {
                            me.showMessage('✅ پخش‌کننده ' + name + ' حذف شد.', 'success');
                        }
                        if (typeof window.loadDistributors === 'function') {
                            window.loadDistributors();
                        }
                        me.loadDistributors().then(function() { me.renderDistributors(); });
                    } else {
                        const err = (typeof window.extractApiError === 'function') ? window.extractApiError(res) : 'خطا در حذف';
                        if (typeof window.showMsg === 'function') {
                            window.showMsg('addDistributorMsg', '⚠️ ' + err, 'error');
                        } else {
                            me.showMessage('⚠️ ' + err, 'error');
                        }
                    }
                }).catch(function() {
                    if (typeof window.showMsg === 'function') {
                        window.showMsg('addDistributorMsg', '⚠️ خطا در ارتباط با سرور.', 'error');
                    } else {
                        me.showMessage('⚠️ خطا در ارتباط با سرور.', 'error');
                    }
                });
            });
        });
    }

    searchDistributors() {
        const query = (document.getElementById('distributorSearchInput')?.value || '').trim();
        const source = Array.isArray(this.distributors) ? this.distributors : [];

        if (!query) {
            this.renderDistributorList(source);
            return;
        }

        const filtered = source.filter(d => {
            const hay = `${d.full_name || ''} ${d.city || ''} ${d.phone || ''}`;
            return hay.includes(query);
        });

        if (filtered.length === 0) {
            const container = document.getElementById('distributorTableBody');
            if (container) {
                container.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align:center;padding:30px;color:var(--text-gray);">
                            هیچ پخش‌کننده‌ای برای «${query}» یافت نشد.
                        </td>
                    </tr>
                `;
            }
            return;
        }

        this.renderDistributorList(filtered);
    }

    // ========================================
    // RENDER: TRANSACTIONS
    // ========================================

    renderTransactions() {
        const container = document.getElementById('financialTableBody');
        if (!container) return;

        // مالی و حسابداری توسط اسکریپت inline خودش (گزارش مالی واقعی) مدیریت می‌شود.
        if (container.dataset.inlineRendered === '1') return;

        if (!Array.isArray(this.transactions) || this.transactions.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align:center;padding:30px;color:var(--text-gray);">
                        هیچ تراکنشی وجود ندارد.
                    </td>
                </tr>
            `;
            return;
        }

        container.innerHTML = this.transactions.slice(0, 20).map(transaction => `
            <tr>
                <td>#${transaction.id}</td>
                <td>${this.formatDate(transaction.created_at)}</td>
                <td>${transaction.description || '---'}</td>
                <td class="${transaction.transaction_type === 'ORDER_DEBT' ? 'tx-amount minus' : 'tx-amount plus'}">${this.formatPrice(Math.abs(transaction.amount))}</td>
                <td>${transaction.paid_amount ? this.formatPrice(transaction.paid_amount) : '---'}</td>
                <td class="${transaction.balance && transaction.balance > 0 ? 'tx-amount minus' : ''}">${this.formatPrice(transaction.balance || 0)}</td>
                <td>${transaction.payment_method || '---'}</td>
                <td><span class="status-badge ${transaction.status === 'SUCCESS' ? 'paid' : 'waiting'}">${transaction.status_label || transaction.status || 'در انتظار'}</span></td>
                <td>${transaction.payment_receipt ? `<a href="${transaction.payment_receipt}" target="_blank" rel="noopener" style="text-decoration:none;" class="btn-secondary btn-sm"><i class="fas fa-paperclip"></i> رسید</a>` : '---'}</td>
            </tr>
        `).join('');
    }

    // ========================================
    // RENDER: CHECKS
    // ========================================

    renderChecks() {
        const container = document.getElementById('checksTableBody');
        if (!container) return;

        const all = Array.isArray(this.checks) ? this.checks : [];
        const query = (this._checksQuery || '').toString().trim();

        let filtered = all;
        if (query) {
            const q = query.toLowerCase();
            filtered = all.filter(check => {
                const cust = this._checkCustomer(check);
                const hay = [
                    cust?.company_name, cust?.full_name, cust?.phone,
                    cust?.national_id, check.check_number, check.bank_name
                ].filter(Boolean).join(' ').toLowerCase();
                return hay.includes(q);
            });
        }

        this._checksFiltered = filtered;

        if (!Array.isArray(filtered) || filtered.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="13" style="text-align:center;padding:30px;color:var(--text-gray);">
                        <i class="fas fa-money-check-alt" style="font-size:24px;display:block;margin-bottom:10px;color:var(--mustard-yellow);"></i>
                        هیچ چکی ثبت نشده است.
                    </td>
                </tr>
            `;
            const pag = document.getElementById('checksPagination');
            if (pag) pag.innerHTML = '';
            return;
        }

        const pageSize = 8;
        const totalPages = Math.ceil(filtered.length / pageSize);
        if (this._checksPage > totalPages) this._checksPage = totalPages;
        if (this._checksPage < 1) this._checksPage = 1;
        const start = (this._checksPage - 1) * pageSize;
        const pageData = filtered.slice(start, start + pageSize);

        container.innerHTML = pageData.map((check, index) => {
            const cust = this._checkCustomer(check);
            const cname = cust?.company_name || cust?.full_name || 'نامشخص';
            const cphone = cust?.phone || '---';
            const cnid = cust?.national_id || '---';
            const statusMeta = this._checkStatusMeta(check.status);
            let actions = '';
            if (check.status === 'PENDING') {
                actions += `<button class="btn-success btn-sm approve-check" data-id="${check.id}" title="تایید چک"><i class="fas fa-check-circle"></i> تایید</button> `;
                actions += `<button class="btn-danger btn-sm reject-check" data-id="${check.id}" title="رد چک"><i class="fas fa-times-circle"></i> رد</button> `;
            }
            if (check.status === 'PENDING' || check.status === 'APPROVED') {
                actions += `<button class="btn-primary btn-sm cash-check" data-id="${check.id}"><i class="fas fa-money-bill-wave"></i> نقد شد</button> `;
            }
            if (check.status !== 'PAID') {
                actions += `<button class="btn-secondary btn-sm delete-check" data-id="${check.id}"><i class="fas fa-trash"></i> حذف</button> `;
            }
            actions += `<button class="btn-secondary btn-sm view-check-files" data-id="${check.id}" title="مشاهده فایل"><i class="fas fa-eye"></i></button>`;
            return `
            <tr data-check-id="${check.id}">
                <td>${start + index + 1}</td>
                <td><strong style="color:var(--text-light);">${cname}</strong></td>
                <td>${cphone}</td>
                <td>${cnid}</td>
                <td>${check.check_number || '---'}</td>
                <td>${check.bank_name || '---'}</td>
                <td>${this.formatPrice(check.amount)}</td>
                <td>${this.formatDate(check.issue_date || check.created_at)}</td>
                <td>${this.formatDate(check.due_date)}</td>
                <td>${check.image ? `<span class="file-item"><i class="fas fa-image"></i> تصویر</span><img src="${this.mediaUrl(check.image)}" alt="چک" style="width:56px;height:38px;object-fit:cover;border-radius:6px;margin-top:4px;" />` : '<span style="color:var(--text-gray);font-size:12px;">بدون فایل</span>'}</td>
                <td><span class="status-badge" style="background:${statusMeta.color};color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;">${statusMeta.label}</span></td>
                <td>${check.registered_by_label || 'منشی'}</td>
                <td>${actions}</td>
            </tr>
            `;
        }).join('');

        this.renderChecksPagination(totalPages);
    }

    renderChecksPagination(totalPages) {
        const container = document.getElementById('checksPagination');
        if (!container) return;
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        let html = `<button class="prev-btn" ${this._checksPage === 1 ? 'disabled' : ''} data-page="${this._checksPage - 1}">قبلی</button>`;
        for (let i = 1; i <= totalPages; i++) {
            html += `<button class="${i === this._checksPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        html += `<button class="next-btn" ${this._checksPage === totalPages ? 'disabled' : ''} data-page="${this._checksPage + 1}">بعدی</button>`;
        container.innerHTML = html;
        container.querySelectorAll('button[data-page]').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = parseInt(btn.dataset.page);
                if (page >= 1 && page <= totalPages && page !== this._checksPage) {
                    this._checksPage = page;
                    this.renderChecks();
                }
            });
        });
    }

    _checkCustomer(check) {
        if (check && check.customer && typeof check.customer === 'object') return check.customer;
        if (check && check.customer_info && typeof check.customer_info === 'object') return check.customer_info;
        if (check && check.customer && Array.isArray(this.customers)) {
            return this.customers.find(c => c.id === check.customer) || null;
        }
        return null;
    }

    _checkStatusMeta(status) {
        const map = {
            'PENDING':  { label: 'در انتظار بررسی', color: '#f1c40f' },
            'APPROVED': { label: 'تایید شده',        color: '#2ecc71' },
            'REJECTED': { label: 'رد شده',           color: '#e74c3c' },
            'PAID':     { label: 'پرداخت شده',       color: '#27ae60' }
        };
        return map[status] || { label: status || '---', color: '#95a5a6' };
    }

    async refreshFinancialAfterCheque() {
        try {
            if (typeof window.loadFinancialData === 'function') window.loadFinancialData();
        } catch (e) { /* noop */ }
        try {
            await this.loadDashboard();
            this.renderDashboard();
        } catch (e) { /* noop */ }
        try {
            await this.loadTransactions();
            this.renderTransactions();
        } catch (e) { /* noop */ }
    }

    // ========================================
    // RENDER: INVENTORY
    // ========================================

    renderInventory() {
        const lowStockItems = Array.isArray(this.inventory) ? this.inventory.filter(item => item.quantity <= item.minimum_stock) : [];
        const lowStockCount = lowStockItems.length;

        const badge = document.querySelector('.panel-badge .low-stock-count');
        if (badge) {
            badge.textContent = lowStockCount;
        }
    }

    // ========================================
    // RENDER: NOTIFICATIONS
    // ========================================

    renderNotifications() {
        const container = document.getElementById('notifList');
        if (!container) return;

        if (!Array.isArray(this.notifications) || this.notifications.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:30px;color:var(--text-gray);">
                    <i class="fas fa-bell-slash" style="font-size:30px;display:block;margin-bottom:12px;"></i>
                    هیچ اعلانی وجود ندارد.
                </div>
            `;
            return;
        }

        container.innerHTML = this.notifications.slice(0, 10).map(notif => `
            <div class="notif-item" data-notif="${notif.id}" style="${notif.is_read ? '' : 'border-right-color: #e74c3c;'}">
                <span class="notif-text">
                    <i class="fas ${this.getNotificationIcon(notif.type)}"></i>
                    ${notif.title}
                </span>
                <span class="notif-time">${this.formatDate(notif.created_at)}</span>
                ${!notif.is_read ? `<button class="btn-secondary btn-sm mark-read" data-id="${notif.id}">خوانده شد</button>` : ''}
            </div>
        `).join('');
    }

    // ========================================
    // UPDATE: HEADER STATS
    // ========================================

    updateHeaderStats() {
        const data = this.dashboardData;
        if (!data) return;

        this.updateElement('ordersTodayCount', data.today?.orders_count || 0);
        this.updateElement('newCustomersCount', data.today?.new_customers || 0);
        this.updateElement('incomeToday', this.formatPrice(data.today?.income || 0));
        this.updateElement('openTicketsBadge', data.summary?.open_tickets || 0);
    }

    // ========================================
    // UPDATE: NOTIFICATION BADGE
    // ========================================

    updateNotificationBadge() {
        const unreadCount = Array.isArray(this.notifications) ? this.notifications.filter(n => !n.is_read).length : 0;
        const badge = document.getElementById('notifBadge');
        if (badge) {
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? '' : 'none';
        }
    }

    // ========================================
    // EVENT LISTENERS (همون قبلی)
    // ========================================

    setupEventListeners() {
        // ===== تیکت‌ها =====
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.answer-ticket')) {
                const btn = e.target.closest('.answer-ticket');
                const id = btn.dataset.id;
                const ticket = Array.isArray(this.tickets) ? this.tickets.find(t => t.id == id) : null;
                if (ticket) {
                    this.showTicketDetail(ticket);
                    const replyInput = document.getElementById('replyInput');
                    if (replyInput) {
                        setTimeout(() => replyInput.focus(), 100);
                    }
                }
            }

            if (e.target.closest('.view-ticket')) {
                const btn = e.target.closest('.view-ticket');
                const id = btn.dataset.id;
                const ticket = Array.isArray(this.tickets) ? this.tickets.find(t => t.id == id) : null;
                if (ticket) {
                    this.showTicketDetail(ticket);
                }
            }

            if (e.target.closest('.note-ticket')) {
                const btn = e.target.closest('.note-ticket');
                const id = btn.dataset.id;
                const note = prompt('متن یادداشت را وارد کنید:');
                if (note && note.trim()) {
                    const response = await apiPost(`tickets/${id}/add_note/`, {
                        note: note.trim()
                    });
                    if (response.success) {
                        this.showSuccess('یادداشت با موفقیت ذخیره شد');
                    } else {
                        this.showError('خطا در ذخیره یادداشت');
                    }
                }
            }
        });

        // ===== مشتریان =====
        document.addEventListener('click', (e) => {
            if (e.target.closest('.view-customer')) {
                const listEl = document.getElementById('customerList');
                if (listEl && listEl.dataset.inlineRendered === '1') return;
                const btn = e.target.closest('.view-customer');
                const id = btn.dataset.id;
                const customer = Array.isArray(this.customers) ? this.customers.find(c => c.id == id) : null;
                if (customer) {
                    this.showCustomerProfile(customer);
                }
            }
        });

        // ===== سفارشات =====
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.view-order')) {
                const btn = e.target.closest('.view-order');
                const id = btn.dataset.id;
                const order = Array.isArray(this.orders) ? this.orders.find(o => String(o.id) === String(id)) : null;
                if (order) {
                    this.openOrderDetail(order);
                } else {
                    const response = await apiGet(`orders/${id}/`);
                    if (response.success) {
                        this.openOrderDetail(response.data);
                    } else {
                        this.showError('خطا در دریافت جزئیات فاکتور');
                    }
                }
            }

            if (e.target.closest('.view-receipt')) {
                const btn = e.target.closest('.view-receipt');
                const id = btn.dataset.order;
                const order = Array.isArray(this.orders) ? this.orders.find(o => String(o.id) === String(id)) : null;
                if (order) {
                    this.openReceiptModal(this.getOrderReceipts(order));
                } else {
                    const response = await apiGet(`orders/${id}/`);
                    if (response.success) {
                        this.openReceiptModal(this.getOrderReceipts(response.data));
                    }
                }
            }

            if (e.target.closest('.approve-invoice')) {
                const btn = e.target.closest('.approve-invoice');
                await this.performConfirm(btn.dataset.id);
            }

            if (e.target.closest('.reject-invoice')) {
                const btn = e.target.closest('.reject-invoice');
                await this.performCancel(btn.dataset.id);
            }

            if (e.target.closest('.print-invoice-btn')) {
                const btn = e.target.closest('.print-invoice-btn');
                const id = btn.dataset.id;
                let order = Array.isArray(this.orders) ? this.orders.find(o => String(o.id) === String(id)) : null;
                if (!order) {
                    const response = await apiGet(`orders/${id}/`);
                    if (response.success) order = response.data;
                }
                if (order) this.printOrderInvoice(order);
            }
        });

        // ===== چک‌ها =====
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.approve-check')) {
                const btn = e.target.closest('.approve-check');
                const id = btn.dataset.id;
                if (confirm('آیا از تایید این چک اطمینان دارید؟')) {
                    const response = await apiPost(`finance/checks/${id}/approve/`);
                    if (response.success) {
                        this.showSuccess('چک با موفقیت تایید شد');
                        await this.loadChecks();
                        this.renderChecks();
                    } else {
                        this.showError('خطا در تایید چک: ' + ((response.data && (response.data.detail || response.data.error)) || 'خطا'));
                    }
                }
            }

            if (e.target.closest('.reject-check')) {
                const btn = e.target.closest('.reject-check');
                const id = btn.dataset.id;
                if (confirm('آیا از رد این چک اطمینان دارید؟')) {
                    const response = await apiPost(`finance/checks/${id}/reject/`);
                    if (response.success) {
                        this.showSuccess('چک رد شد');
                        await this.loadChecks();
                        this.renderChecks();
                    } else {
                        this.showError('خطا در رد چک: ' + ((response.data && (response.data.detail || response.data.error)) || 'خطا'));
                    }
                }
            }

            if (e.target.closest('.cash-check')) {
                const btn = e.target.closest('.cash-check');
                const id = btn.dataset.id;
                if (confirm('آیا از نقد شدن این چک اطمینان دارید؟')) {
                    const response = await apiPost(`finance/checks/${id}/cash_check/`);
                    if (response.success) {
                        this.showSuccess('چک با موفقیت نقد شد');
                        await this.loadChecks();
                        this.renderChecks();
                        this.refreshFinancialAfterCheque();
                    } else {
                        this.showError('خطا در نقد کردن چک');
                    }
                }
            }

            if (e.target.closest('.delete-check')) {
                const btn = e.target.closest('.delete-check');
                const id = btn.dataset.id;
                if (confirm('آیا از حذف این چک اطمینان دارید؟')) {
                    const response = await apiDelete(`finance/checks/${id}/`);
                    if (response.success) {
                        this.showSuccess('چک با موفقیت حذف شد');
                        await this.loadChecks();
                        this.renderChecks();
                    } else {
                        this.showError('خطا در حذف چک');
                    }
                }
            }

            if (e.target.closest('.view-check-files')) {
                const btn = e.target.closest('.view-check-files');
                const id = parseInt(btn.dataset.id);
                const cheque = (Array.isArray(this.checks) ? this.checks : []).find(c => Number(c.id) === Number(id));
                const modal = document.getElementById('checkFilesModal');
                const list = document.getElementById('checkFilesList');
                if (!modal || !list) return;
                if (cheque && cheque.image) {
                    list.innerHTML = `<div class="file-item"><i class="fas fa-image"></i> تصویر چک</div><img src="${this.mediaUrl(cheque.image)}" alt="چک" style="max-width:100%;border-radius:8px;margin-top:8px;" />`;
                } else {
                    list.innerHTML = `<div style="color:var(--text-gray);font-size:13px;">فایلی برای این چک ثبت نشده است.</div>`;
                }
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });

        // ===== اعلانات =====
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.mark-read')) {
                const btn = e.target.closest('.mark-read');
                const id = btn.dataset.id;
                const response = await apiPost(`notifications/${id}/mark_as_read/`);
                if (response.success) {
                    await this.loadNotifications();
                    this.renderNotifications();
                    this.updateNotificationBadge();
                }
            }
        });

        // ===== دکمه بستن پنل =====
        document.getElementById('closePanelBtn')?.addEventListener('click', () => {
            if (confirm('آیا از خروج از پنل اطمینان دارید؟')) {
                window.location.href = 'index.html';
            }
        });

        // ===== دکمه خروج =====
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            if (confirm('آیا از خروج اطمینان دارید؟')) {
                clearTokens();
                window.location.href = 'log.html';
            }
        });

        // ===== فیلتر تیکت =====
        document.getElementById('applyTicketFilter')?.addEventListener('click', () => {
            this.filterTickets();
        });
        document.getElementById('resetTicketFilter')?.addEventListener('click', () => {
            document.getElementById('ticketStatusFilter').value = 'all';
            document.getElementById('ticketSenderFilter').value = 'all';
            document.querySelectorAll('#ticketList .ticket-item').forEach(item => {
                item.style.display = '';
            });
            this.showSuccess('فیلتر تیکت حذف شد');
        });

        // ===== افزودن توزیع‌کننده =====
        document.getElementById('saveNewDistributorBtn')?.addEventListener('click', async () => {
            const name = document.getElementById('newDistributorName')?.value?.trim();
            const username = document.getElementById('newDistributorUsername')?.value?.trim();
            const password = document.getElementById('newDistributorPassword')?.value?.trim();
            const city = document.getElementById('newDistributorCity')?.value?.trim();
            const phone = document.getElementById('newDistributorPhone')?.value?.trim();

            if (!name || !username || !password || !city) {
                this.showError('لطفاً تمام فیلدهای الزامی را پر کنید');
                return;
            }

            if (password.length < 4) {
                this.showError('رمز عبور باید حداقل ۴ کاراکتر باشد');
                return;
            }

            const response = await apiPost('distributors/', {
                username: username,
                password: password,
                full_name: name,
                city: city,
                phone: phone || ''
            });

            if (response.success) {
                this.showSuccess('توزیع‌کننده با موفقیت اضافه شد');
                await this.loadDistributors();
                this.renderDistributors();
                const form = document.getElementById('addDistributorForm');
                if (form) form.classList.remove('active');
                const toggleBtn = document.getElementById('showAddDistributorBtn');
                if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-plus"></i> افزودن پخش‌کننده';
                ['newDistributorName', 'newDistributorUsername', 'newDistributorPassword', 'newDistributorCity', 'newDistributorPhone'].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.value = '';
                });
            } else {
                this.showError('خطا در افزودن توزیع‌کننده: ' + JSON.stringify(response.data));
            }
        });

        // ===== جستجوی توزیع‌کننده =====
        document.getElementById('searchDistributorBtn')?.addEventListener('click', () => {
            this.searchDistributors();
        });
        document.getElementById('distributorSearchInput')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.searchDistributors();
        });
        document.getElementById('distributorSearchInput')?.addEventListener('input', (e) => {
            if (!e.target.value) this.renderDistributors();
        });

        // ===== افزودن چک =====
        document.getElementById('saveCheckBtn')?.addEventListener('click', async () => {
            const name = document.getElementById('checkName')?.value?.trim();
            const phone = document.getElementById('checkPhone')?.value?.trim();
            const nationalId = document.getElementById('checkNationalId')?.value?.trim();
            const amount = document.getElementById('checkAmount')?.value?.trim();
            const receiveDate = document.getElementById('checkReceiveDate')?.value;
            const dueDate = document.getElementById('checkDueDate')?.value;

            if (!name || !phone || !nationalId || !amount || !receiveDate || !dueDate) {
                this.showError('لطفاً تمام فیلدهای الزامی را پر کنید');
                return;
            }

            const customer = Array.isArray(this.customers) ? this.customers.find(c => c.phone === phone) : null;
            let customerId = customer ? customer.id : null;

            if (!customerId) {
                const createResp = await apiPost('customers/', {
                    username: 'cust_' + phone.replace(/[^A-Za-z0-9]/g, '') + '_' + Math.floor(Math.random() * 100000),
                    password: 'Cust@' + Date.now() % 1000000,
                    company_name: name,
                    phone: phone,
                    national_id: nationalId
                });

                if (!createResp.success || !createResp.data?.id) {
                    await this.loadCustomers();
                    const again = Array.isArray(this.customers) ? this.customers.find(c => c.phone === phone) : null;
                    customerId = again ? again.id : null;
                } else {
                    customerId = createResp.data.id;
                    await this.loadCustomers();
                }

                if (!customerId) {
                    this.showError('خطا در ایجاد مشتری جدید');
                    return;
                }
            }

            const fileInput = document.getElementById('checkFile');
            let imageFile = null;
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                imageFile = fileInput.files[0];
                if (imageFile && !/^image\//.test(imageFile.type || '')) {
                    this.showError('فقط فایل تصویری (JPG / PNG / و...) مجاز است');
                    return;
                }
            }

            const fd = new FormData();
            fd.append('customer', customerId);
            fd.append('check_number', `CHK-${Date.now()}`);
            fd.append('bank_name', 'بانک ملی');
            fd.append('amount', parseInt(amount));
            fd.append('issue_date', receiveDate);
            fd.append('due_date', dueDate);
            fd.append('status', 'PENDING');
            if (imageFile) fd.append('image', imageFile);

            const response = await apiUpload('finance/checks/', fd);

            if (response.success) {
                this.showSuccess('چک با موفقیت ثبت شد');
                this._checksPage = 1;
                await this.loadChecks();
                this.renderChecks();
                document.getElementById('addCheckForm').classList.remove('active');
                const toggleBtn = document.getElementById('showAddCheckBtn');
                if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-plus"></i> افزودن چک جدید';
                if (fileInput) fileInput.value = '';
                const preview = document.getElementById('checkFileList');
                if (preview) preview.innerHTML = '';
            } else {
                this.showError('خطا در ثبت چک: ' + JSON.stringify(response.data));
            }
        });

        // ===== جستجوی چک =====
        document.getElementById('searchCheckBtn')?.addEventListener('click', () => {
            this._checksQuery = document.getElementById('checkSearchInput')?.value?.trim() || '';
            this._checksPage = 1;
            this.renderChecks();
            const msg = document.getElementById('checksMsg');
            if (msg) {
                const count = Array.isArray(this._checksFiltered) ? this._checksFiltered.length : 0;
                msg.innerHTML = `<span style="color:var(--text-gray);font-size:12px;">🔍 ${count} نتیجه یافت شد.</span>`;
            }
        });
        document.getElementById('checkSearchInput')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') document.getElementById('searchCheckBtn')?.click();
        });
        document.getElementById('checkSearchInput')?.addEventListener('input', (e) => {
            if (!e.target.value) {
                this._checksQuery = '';
                this._checksPage = 1;
                this.renderChecks();
            }
        });

        // ===== نمایش/بستن فرم افزودن چک =====
        document.getElementById('showAddCheckBtn')?.addEventListener('click', function() {
            const form = document.getElementById('addCheckForm');
            if (!form) return;
            form.classList.toggle('active');
            this.innerHTML = form.classList.contains('active') ? '<i class="fas fa-times"></i> بستن فرم' : '<i class="fas fa-plus"></i> افزودن چک جدید';
            const msg = document.getElementById('addCheckMsg');
            if (msg) msg.innerHTML = '';
            const today = new Date().toISOString().split('T')[0];
            const recv = document.getElementById('checkReceiveDate');
            if (recv) recv.value = today;
            const due = new Date();
            due.setDate(due.getDate() + 30);
            const dueEl = document.getElementById('checkDueDate');
            if (dueEl) dueEl.value = due.toISOString().split('T')[0];
        });
        document.getElementById('cancelAddCheckBtn')?.addEventListener('click', function() {
            document.getElementById('addCheckForm')?.classList.remove('active');
            const toggleBtn = document.getElementById('showAddCheckBtn');
            if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-plus"></i> افزودن چک جدید';
            const msg = document.getElementById('addCheckMsg');
            if (msg) msg.innerHTML = '';
        });

        // ===== پیش‌نمایش فایل‌های چک =====
        document.getElementById('checkFile')?.addEventListener('change', function() {
            const list = document.getElementById('checkFileList');
            if (!list) return;
            list.innerHTML = '';
            const files = this.files || [];
            for (let i = 0; i < files.length; i++) {
                const span = document.createElement('span');
                span.className = 'file-item';
                span.innerHTML = `<i class="fas fa-paperclip"></i> ${files[i].name}`;
                list.appendChild(span);
            }
        });

        // ===== بستن مودال فایل‌های چک =====
        document.getElementById('closeCheckFilesModal')?.addEventListener('click', function() {
            document.getElementById('checkFilesModal')?.classList.remove('active');
            document.body.style.overflow = '';
        });
        const checkFilesModal = document.getElementById('checkFilesModal');
        if (checkFilesModal) {
            checkFilesModal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        }

        // ===== اضافه کردن محصول =====
        document.getElementById('addProductBtn')?.addEventListener('click', () => {
            this.showAddProductModal();
        });

        // ===== اضافه کردن تخفیف =====
        document.getElementById('addDiscountBtn')?.addEventListener('click', () => {
            this.showAddDiscountModal();
        });
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    formatPrice(price) {
        if (!price && price !== 0) return '۰';
        return Math.round(price).toLocaleString('fa-IR') + ' تومان';
    }

    formatDate(date) {
        if (!date) return '---';
        try {
            const d = new Date(date);
            return d.toLocaleDateString('fa-IR') + ' ' + d.toLocaleTimeString('fa-IR');
        } catch {
            return date;
        }
    }

    mediaUrl(path) {
        if (!path) return '';
        if (/^https?:\/\//.test(path)) return path;
        let base = '';
        try {
            base = (typeof API_URL === 'string' ? API_URL : '').replace(/\/api\/?$/, '');
        } catch (e) { /* noop */ }
        return base + (path.startsWith('/') ? path : '/' + path);
    }

    getDayName(day) {
        const days = {
            'Saturday': 'شنبه',
            'Sunday': 'یکشنبه',
            'Monday': 'دوشنبه',
            'Tuesday': 'سه‌شنبه',
            'Wednesday': 'چهارشنبه',
            'Thursday': 'پنجشنبه',
            'Friday': 'جمعه'
        };
        return days[day] || day;
    }

    getOrderStatusClass(status) {
        const map = {
            'PENDING': 'waiting',
            'CONFIRMED': 'processing',
            'PREPARING': 'processing',
            'SHIPPED': 'shipped',
            'DELIVERED': 'delivered',
            'CANCELLED': 'canceled'
        };
        return map[status] || 'waiting';
    }

    getPaymentMethodLabel(method) {
        const map = {
            'ONLINE': 'پرداخت آنلاین',
            'CARD': 'کارت به کارت',
            'CASH': 'پرداخت نقدی',
            'CHECK': 'پرداخت چکی',
            'BALANCE': 'کیف پول'
        };
        return map[method] || method || '---';
    }

    getOrderStatusLabel(status) {
        const map = {
            'PENDING': 'در انتظار',
            'CONFIRMED': 'تایید شده',
            'PREPARING': 'در حال آماده‌سازی',
            'SHIPPED': 'ارسال شده',
            'DELIVERED': 'تحویل شده',
            'CANCELLED': 'لغو شده'
        };
        return map[status] || status;
    }

    getNotificationIcon(type) {
        const map = {
            'INFO': 'fa-info-circle',
            'OFFER': 'fa-tag',
            'WARNING': 'fa-exclamation-triangle',
            'MESSAGE': 'fa-envelope'
        };
        return map[type] || 'fa-bell';
    }

    // ========================================
    // MODALS
    // ========================================

    showTicketDetail(ticket) {
        const detail = document.getElementById('ticketDetail');
        if (!detail) return;

        this.currentTicket = ticket;

        const roleLabels = {
            'CUSTOMER': 'مشتری',
            'DISTRIBUTOR': 'توزیع‌کننده',
            'ADMIN': 'ادمین',
            'SECRETARY': 'منشی',
            'GUEST': 'مهمان'
        };
        const senderName = ticket.user_name || ticket.user?.username || (ticket.guest_name || 'مهمان');
        const senderPhone = ticket.user_phone || ticket.guest_phone || '—';
        const senderCompany = ticket.user_company || '';
        const senderRole = roleLabels[ticket.user_role] || roleLabels[ticket.user?.role] || 'مشتری';

        document.getElementById('detailTitle').innerHTML = `
            <i class="fas fa-ticket-alt"></i> ${this.escapeHtml(ticket.title)}
            <span style="font-size:12px;font-weight:400;color:var(--text-gray);margin-right:10px;display:block;margin-top:4px;">
                <i class="fas fa-user"></i> ${this.escapeHtml(senderName)}
                ${senderCompany ? ` <i class="fas fa-building"></i> ${this.escapeHtml(senderCompany)}` : ''}
                <i class="fas fa-phone"></i> ${this.escapeHtml(senderPhone)}
                <span class="status-badge pending" style="font-size:10px;margin-right:6px;">${senderRole}</span>
            </span>`;

        const messages = document.getElementById('detailMessages');
        const items = this.buildTicketThread(ticket);
        messages.innerHTML = items.map(m => {
            const attaches = (Array.isArray(m.attachments) ? m.attachments : [])
                .map(a => this._attachmentBlockHtml(a && a.name, a && a.url, a && a.size))
                .join('');
            return `
            <div class="ticket-msg ${m.type}">
                <strong>${this.escapeHtml(m.name)}</strong><br>
                ${this.escapeHtml(m.text).replace(/\n/g, '<br>')}
                ${attaches}
                <div class="msg-meta">
                    <span>${m.time}</span>
                </div>
            </div>
        `;
        }).join('') || '<div style="text-align:center;color:var(--text-gray);padding:20px;">هیچ پیامی وجود ندارد</div>';

        messages.scrollTop = messages.scrollHeight;

        detail.classList.add('active');
    }

    _attachmentBlockHtml(name, url, size) {
        if (!url) return '';
        const full = this.mediaUrl(url);
        const isImage = /\.(png|jpe?g|gif|webp|bmp|svg|heic|avif|jpg)$/i.test(name || '');
        const sizeTxt = size ? ' (' + this.formatFileSize(size) + ')' : '';
        const label = `<i class="fas ${isImage ? 'fa-image' : 'fa-paperclip'}"></i> ${this.escapeHtml(name || 'پیوست')}${sizeTxt ? `<span class="attach-size">${sizeTxt}</span>` : ''}`;
        const link = `<div class="ticket-attach"><a href="${this.escapeHtml(full)}" target="_blank" rel="noopener">${label}</a></div>`;
        if (!isImage) return link;
        return `<div class="ticket-attach-img"><a href="${this.escapeHtml(full)}" target="_blank" rel="noopener"><img src="${this.escapeHtml(full)}" alt="${this.escapeHtml(name || '')}" /></a></div>`;
    }

    formatFileSize(bytes) {
        bytes = Number(bytes) || 0;
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    buildTicketThread(ticket) {
        const fmt = (d) => this.formatDate(d);
        const items = [];

        if (Array.isArray(ticket.messages) && ticket.messages.length > 0) {
            ticket.messages.forEach(msg => {
                const isStaff = msg.sender === 'STAFF';
                items.push({
                    type: isStaff ? 'admin' : 'user',
                    name: msg.sender_name || (isStaff ? 'پشتیبانی' : 'مشتری'),
                    text: msg.text || '',
                    attachments: msg.attachments || [],
                    time: fmt(msg.created_at)
                });
            });
            return items;
        }

        if (ticket.message) {
            items.push({
                type: 'user',
                name: ticket.user_name || ticket.user?.username || 'مشتری',
                text: ticket.message,
                time: fmt(ticket.created_at)
            });
        }
        if (ticket.admin_reply) {
            items.push({
                type: 'admin',
                name: 'پشتیبانی',
                text: ticket.admin_reply,
                time: fmt(ticket.admin_replied_at)
            });
        }
        if (ticket.customer_reply) {
            items.push({
                type: 'user',
                name: ticket.user_name || ticket.user?.username || 'مشتری',
                text: ticket.customer_reply,
                time: fmt(ticket.customer_replied_at)
            });
        }
        return items;
    }

    async sendReplyFromChat() {
        const replyInput = document.getElementById('replyInput');
        const msgBox = document.getElementById('replyMsg');
        const reply = replyInput ? replyInput.value.trim() : '';
        const files = Array.isArray(this._replyFiles) ? this._replyFiles : [];
        await this._submitTicketReply(reply, files, msgBox);
        if (replyInput) replyInput.value = '';
        this._replyFiles = [];
        this._refreshReplyFiles();
    }

    async sendReplyFromModal() {
        const textInput = document.getElementById('replyModalText');
        const modalInput = document.getElementById('replyFileInput');
        const msgBox = document.getElementById('modalReplyMsg');
        const reply = textInput ? textInput.value.trim() : '';
        const files = modalInput && modalInput.files ? Array.from(modalInput.files) : [];
        const ok = await this._submitTicketReply(reply, files, msgBox);
        if (ok) {
            if (textInput) textInput.value = '';
            if (modalInput) modalInput.value = '';
            const modal = document.getElementById('ticketReplyModal');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        }
    }

    setReplyFiles(fileList) {
        this._replyFiles = fileList ? Array.from(fileList) : [];
        this._refreshReplyFiles();
    }

    _refreshReplyFiles() {
        const el = document.getElementById('detailAttachments');
        if (!el) return;
        const files = Array.isArray(this._replyFiles) ? this._replyFiles : [];
        el.innerHTML = files.length
            ? files.map(f => `<span class="file-item"><i class="fas fa-paperclip"></i> ${this.escapeHtml(f.name)}</span>`).join('')
            : '';
    }

    async _submitTicketReply(reply, files, msgBox) {
        const showMsgInBox = (html) => {
            if (msgBox) msgBox.innerHTML = `<div class="operation-msg ${html.type}">${html.text}</div>`;
        };

        const hasFiles = Array.isArray(files) && files.length > 0;
        if (!reply && !hasFiles) {
            showMsgInBox({ type: 'error', text: '⚠️ لطفاً متن پاسخ یا فایل پیوست را وارد کنید.' });
            return false;
        }

        const ticket = this.currentTicket;
        if (!ticket) {
            showMsgInBox({ type: 'error', text: '⚠️ ابتدا یک تیکت را باز کنید.' });
            return false;
        }

        const formData = new FormData();
        if (reply) formData.append('reply_message', reply);
        (files || []).forEach(f => formData.append('attachments', f, f.name));

        const response = await apiUpload(`tickets/${ticket.id}/reply/`, formData);

        if (response && response.success) {
            showMsgInBox({ type: 'success', text: '✅ پاسخ با موفقیت ارسال شد.' });
            await this.loadTickets();
            this.renderTickets();
            this.renderRequests();
            const updated = Array.isArray(this.tickets) ? this.tickets.find(t => t.id == ticket.id) : null;
            if (updated) this.showTicketDetail(updated);
            return true;
        } else {
            const detail = (response && response.data && (response.data.error || response.data.detail)) || '';
            showMsgInBox({ type: 'error', text: '❌ خطا در ارسال پاسخ.' + (detail ? ' ' + detail : '') });
            return false;
        }
    }

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    showCustomerProfile(customer) {
        alert(`پروفایل مشتری: ${customer.company_name || customer.full_name}\nتلفن: ${customer.phone}\nکد: ${customer.customer_code}`);
    }

    // ========================================
    // showAddProductModal - اصلاح شده
    // ========================================

    showAddProductModal() {
        const name = prompt('نام محصول:');
        if (name && name.trim()) {
            const price = prompt('قیمت پایه (تومان):');
            if (price && !isNaN(price) && parseInt(price) > 0) {
                const weight = prompt('وزن (گرم):');
                const meatPercent = prompt('درصد گوشت:');

                apiPost('products/', {
                    name: name.trim(),
                    base_price: parseInt(price),
                    weight: parseInt(weight) || 100,
                    meat_percent: parseInt(meatPercent) || 90,
                    code: `PRD-${Date.now()}`,
                    is_active: true
                }).then(async response => {
                    if (response.success) {
                        this.showSuccess(`محصول ${name} با موفقیت اضافه شد`);
                        await this.loadProducts();
                        this.renderProducts();
                    } else {
                        this.showError('خطا در افزودن محصول');
                    }
                });
            }
        }
    }

    showAddDiscountModal() {
        const code = prompt('کد تخفیف:');
        if (code && code.trim()) {
            const percent = prompt('درصد تخفیف:');
            if (percent && !isNaN(percent) && parseInt(percent) > 0) {
                this.showSuccess(`کد تخفیف ${code.trim()} با ${percent}% ایجاد شد`);
            }
        }
    }

    // ========================================
    // FILTERS
    // ========================================

    filterTickets() {
        const status = document.getElementById('ticketStatusFilter').value;
        const sender = document.getElementById('ticketSenderFilter').value;

        document.querySelectorAll('#ticketList .ticket-item').forEach(item => {
            let show = true;
            const itemStatus = item.dataset.status || 'unanswered';
            const itemSender = item.dataset.sender || 'customer';

            if (status !== 'all') {
                if (status === 'answered' && itemStatus !== 'ANSWERED') show = false;
                if (status === 'unanswered' && itemStatus === 'ANSWERED') show = false;
            }
            if (sender !== 'all' && itemSender !== sender) show = false;

            item.style.display = show ? '' : 'none';
        });

        this.showSuccess('فیلتر تیکت اعمال شد');
    }

    // ========================================
    // NOTIFICATIONS
    // ========================================

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const container = document.getElementById('globalMessage');
        if (!container) {
            const div = document.createElement('div');
            div.id = 'globalMessage';
            div.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                padding: 16px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
                min-width: 300px;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
                opacity: 0;
                transform: translateY(-20px);
            `;
            document.body.appendChild(div);
        }

        const el = document.getElementById('globalMessage');
        el.textContent = message;
        el.style.background = type === 'success' ? '#2ecc71' : '#e74c3c';
        el.style.color = '#fff';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';

        clearTimeout(el._timeout);
        el._timeout = setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-20px)';
        }, 3000);
    }
}

// ========================================
// INIT
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    window.secretaryPanel = new SecretaryPanel();
});

console.log('✅ پنل منشی بارگذاری شد!');
