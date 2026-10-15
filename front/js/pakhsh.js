// ================================================================
// پنل پخش‌کننده (Distributor Panel) - نسخه واقعی متصل به API
// ================================================================
(function () {
    'use strict';

    // ---------------- ابزارهای کمکی ----------------
    function $id(id) {
        return document.getElementById(id);
    }

    function esc(v) {
        return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function faNum(v) {
        var n = Number(v) || 0;
        return n.toLocaleString('fa-IR');
    }

    function toman(v) {
        return faNum(v) + ' تومان';
    }

    function orderPaid(o) {
        return Number(o && o.paid_amount != null ? o.paid_amount : 0) || 0;
    }

    function orderTotal(o) {
        return Number(o && o.total_price != null ? o.total_price : 0) || 0;
    }

    function orderRemaining(o) {
        if (!o) return 0;
        if (o.remaining_amount != null) return Number(o.remaining_amount) || 0;
        if (o.balance != null) return Number(o.balance) || 0;
        return Math.max(orderTotal(o) - orderPaid(o), 0);
    }

    function faDate(iso) {
        if (!iso) return '—';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return String(iso);
            return d.toLocaleDateString('fa-IR');
        } catch (e) {
            return String(iso);
        }
    }

    function faDateTime(iso) {
        if (!iso) return '—';
        try {
            var d = new Date(iso);
            if (isNaN(d.getTime())) return String(iso);
            return d.toLocaleDateString('fa-IR') + ' − ' + d.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return String(iso);
        }
    }

    function isoDate(d) {
        var t = d || new Date();
        return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0');
    }

    function errMsg(res) {
        if (!res) return 'خطای ارتباط با سرور.';
        if (res.error) return res.error;
        var d = res.data;
        if (!d) return 'خطای ارتباط با سرور.';
        if (typeof d === 'string') return d;
        if (typeof d === 'object') {
            if (d.detail) return d.detail;
            if (d.message) return d.message;
            var keys = Object.keys(d);
            if (keys.length) {
                var k = keys[0];
                var v = d[k];
                if (Array.isArray(v)) return String(v[0]);
                if (typeof v === 'object') {
                    var kk = Object.keys(v);
                    if (kk.length) return String(v[kk[0]] && v[kk[0]][0] ? v[kk[0]][0] : v[kk[0]]);
                }
                return String(v);
            }
        }
        return 'خطای ناشناخته.';
    }

    function renderPanelLoadError(targetId, message, retry) {
        var target = $id(targetId);
        if (!target) return;
        var content = '<i class="fas fa-exclamation-triangle"></i><span>' + esc(message || 'بارگذاری اطلاعات ناموفق بود.') + '</span>' +
            (retry ? '<button type="button" class="btn-secondary btn-sm panel-retry-btn">تلاش دوباره</button>' : '');
        var colspan = 10;
        if (target.tagName === 'TBODY') {
            var table = target.closest('table');
            var header = table && table.querySelector('thead tr');
            if (header && header.children.length) colspan = header.children.length;
        }
        target.innerHTML = target.tagName === 'TBODY'
            ? '<tr><td colspan="' + colspan + '" class="load-error-cell"><div class="load-error">' + content + '</div></td></tr>'
            : '<div class="load-error">' + content + '</div>';
        var button = target.querySelector('.panel-retry-btn');
        if (button && retry) button.addEventListener('click', retry);
    }

    function msgBox(msg, ok) {
        if (!msg) return;
        var box = document.createElement('div');
        box.style.cssText = 'margin-top:12px;padding:10px 14px;border-radius:10px;font-size:13px;color:#fff;background:' +
            (ok ? 'rgba(46,204,113,0.18);border:1px solid rgba(46,204,113,0.3)' : 'rgba(231,76,60,0.18);border:1px solid rgba(231,76,60,0.3)');
        box.textContent = msg;
        return box;
    }

    function statusBadge(key, map) {
        var item = map[key] || map.CANCELLED;
        if (item) {
            return '<span class="status-badge ' + item[1] + '">' + item[0] + '</span>';
        }
        return '<span class="status-badge waiting">' + esc(key) + '</span>';
    }

    var PURCHASE_STATUS = {
        PENDING: ['در انتظار تایید', 'waiting'],
        CONFIRMED: ['تایید شده', 'confirmed'],
        PREPARING: ['در حال آماده‌سازی', 'preparing'],
        SHIPPED: ['ارسال شده', 'shipped'],
        DELIVERED: ['تحویل شده', 'delivered'],
        REJECTED: ['رد شده', 'rejected'],
        CANCELLED: ['لغو شده', 'cancelled']
    };

    var ORDER_STATUS = {
        PENDING: ['در انتظار', 'pending'],
        AWAITING_APPROVAL: ['در انتظار تأیید شما', 'waiting'],
        CONFIRMED: ['تایید شده', 'confirmed'],
        PREPARING: ['در حال آماده‌سازی', 'preparing'],
        SHIPPED: ['ارسال شده', 'shipped'],
        DELIVERED: ['تحویل شده', 'delivered'],
        CANCELLED: ['لغو شده', 'cancelled'],
        RETURNED: ['مرجوع', 'rejected']
    };

    var CHECK_STATUS = {
        PENDING: ['در انتظار', 'uncashed'],
        APPROVED: ['تایید شده', 'approved'],
        REJECTED: ['رد شده', 'rejected'],
        PAID: ['نقد شده', 'cashed']
    };

    var TICKET_STATUS = {
        OPEN: 'پاسخ داده نشده',
        ANSWERED: 'پاسخ داده شده',
        CLOSED: 'بسته شده'
    };

    // ================================================================
    // کلاس اصلی پنل
    // ================================================================
    function DistributorPanel() {
        this.products = [];
        this.productsLoaded = false;
        this.priceMap = {};          // productId -> قیمت خرید از شرکت (DistributorPrice)
        this.customers = [];
        this.custMap = {};           // customerId -> customer
        this.orders = [];
        this.purchases = [];
        this.tickets = [];
        this.checks = [];
        this.discounts = [];
        this.transactions = [];
        this.reminders = [];
        this.smsHistory = [];
        this.reportState = { customers: [], personId: null, person: null, debtors: [], debtorPage: 1, debtorSearch: '', generalRows: [] };
        this.financialData = null;
        this.financialState = { period: 'month', from: '', to: '', granularity: 'daily', customerName: '', invoiceNumber: '' };
        this.me = null;
        this.distributor = null;
        this.dashboard = null;
        this.pendingCustomerPrices = {};
        this.modalPrices = [];
        this.notifications = [];
        this.activeCustPriceTarget = null;
        this.checksQuery = '';
        this.checksPage = 1;
        this.checksPageSize = 5;
        this.discountsPage = 1;
        this.discountsPageSize = 5;
    }

    DistributorPanel.prototype._priceFor = function (productId) {
        var p = this.priceMap[productId];
        if (p != null && p > 0) return Number(p);
        return Number(this.productsById[productId] ? (this.productsById[productId].base_price || 0) : 0);
    };

    // تعداد بسته در هر کارتن (قیمت کارتن = قیمت بسته × این عدد)
    DistributorPanel.prototype._packFor = function (productId) {
        var p = this.productsById[productId];
        var pack = p ? Number(p.pack_per_carton != null ? p.pack_per_carton : p.carton_size) : 0;
        return pack > 0 ? pack : 1;
    };

    DistributorPanel.prototype._linePriceFor = function (productId, unit) {
        var price = this._priceFor(productId) || 0;
        if (unit === 'carton') price = price * this._packFor(productId);
        return price;
    };

    // ================================================================
    // راه‌اندازی
    // ================================================================
    DistributorPanel.prototype.init = function () {
        var me = this;
        var stored = {};
        try { stored = JSON.parse(localStorage.getItem('zamaniCurrentUser') || '{}'); } catch (e) { }

        // The cached profile can be stale after a role change or a fresh login.
        // Use the authenticated backend profile as the source of truth.
        if (!localStorage.getItem('access_token')) {
            window.location.href = 'log.html';
            return;
        }
        this.bindings();
        apiGet('/accounts/me/').then(function (res) {
            if (!res.success || String(res.data && res.data.role || '').toUpperCase() !== 'DISTRIBUTOR') {
                window.location.href = 'log.html';
                return;
            }
            me.me = res.data;
            me.distributor = res.data.distributor || me.distributor;
            localStorage.setItem('zamaniCurrentUser', JSON.stringify(res.data));
            me.loadAll();
        }).catch(function () {
            window.location.href = 'log.html';
        });
    };

    DistributorPanel.prototype.loadAll = function () {
        var me = this;
        this.loadMe();
        this.loadProducts();
        this.loadDashboard();
        this.loadCustomers();
        this.loadOrders();
        this.loadPurchases();
        this.loadTickets();
        this.loadChecks();
        this.loadDiscounts();
        this.loadTransactions();
        this.loadNotifications();
        this.renderInventory();
        this.loadInventoryFromServer();
    };

    DistributorPanel.prototype.loadInventoryFromServer = function () {
        var me = this;
        apiGet('/inventory/?page_size=500').then(function (res) {
            if (!res || !res.success) {
                renderPanelLoadError('companyInventoryGrid', errMsg(res), function () { me.loadInventoryFromServer(); });
                return;
            }
            var rows = Array.isArray(res.data) ? res.data : ((res.data && res.data.results) || []);
            var inv = {};
            rows.forEach(function (row) {
                if (!row.product_name) return;
                inv[row.product_name] = {
                    name: row.product_name,
                    packageQty: Number(row.package_quantity || 0),
                    cartonQty: Number(row.carton_quantity || 0)
                };
            });
            var all = Object.keys(inv).map(function (name) {
                var p = inv[name];
                return { name: p.name, pkg: p.packageQty, carton: p.cartonQty, total: p.packageQty + p.cartonQty };
            });
            var grid = $id('companyInventoryGrid');
            if (!grid) return;
            grid.innerHTML = all.length ? all.map(function (p) {
                return '<div class="inventory-summary-card"><div class="summary-product-name"><i class="fas fa-cube"></i> ' + esc(p.name) + '</div>' +
                    '<div class="summary-values"><div class="summary-item"><span class="summary-label">📦 بسته‌ای</span><span class="summary-value package">' + faNum(p.pkg) + '</span></div>' +
                    '<div class="summary-item"><span class="summary-label">📦 کارتنی</span><span class="summary-value carton">' + faNum(p.carton) + '</span></div></div></div>';
            }).join('') : '<div style="grid-column:1/-1;text-align:center;color:var(--text-gray);padding:18px;font-size:13px;">داده‌ای از انبار شرکت در دسترس نیست.</div>';
        }).catch(function () {
            renderPanelLoadError('companyInventoryGrid', 'بارگذاری انبار شرکت ناموفق بود.', function () { me.loadInventoryFromServer(); });
        });
    };

    DistributorPanel.prototype.loadMe = function () {
        var me = this;
        apiGet('/accounts/me/').then(function (res) {
            if (res.success) {
                me.me = res.data;
                localStorage.setItem('zamaniCurrentUser', JSON.stringify(res.data));
            } else {
                console.warn('loadMe', errMsg(res));
            }
        });
    };

    // ---------------- محصولات و قیمت‌ها ----------------
    DistributorPanel.prototype.loadProducts = function () {
        var me = this;
        apiGet('/products/products/?page_size=2000').then(function (res) {
            if (!res.success) {
                console.warn('products', errMsg(res));
                me.productsLoaded = true;
                me.rebuildCustomerPriceList();
                return;
            }
            var list = res.data.results || res.data || [];
            me.products = list.filter(function (p) {
                var ok = p.is_active !== false;
                if (!ok) return false;
                var code = (p.code || '').toString().toUpperCase();
                var name = (p.name || '').toString();
                // Show only the requested 9 products for customer manual pricing context
                if (code.startsWith('HAM-') || code.startsWith('STK-') || code.startsWith('RST-')) return true;
                // Also allow specific IDs if any
                return ok;
            });
            // Sort for consistency: HAM-90, HAM-60, STK, RST
            me.products.sort(function (a, b) {
                var ca = (a.code || '').toUpperCase();
                var cb = (b.code || '').toUpperCase();
                return ca.localeCompare(cb);
            });
            me.productsLoaded = true;
            me.productsById = {};
            me.products.forEach(function (p) { me.productsById[p.id] = p; });
            apiGet('/pricing/?page_size=500').then(function (pr) {
                if (pr.success) {
                    var plist = pr.data.results || pr.data || [];
                    me.priceMap = {};
                    plist.forEach(function (row) {
                        var pid = row.product != null ? row.product : row.product_id;
                        if (pid != null) me.priceMap[pid] = Number(row.price || 0);
                    });
                }
                me.renderPurchaseSelects();
                me.renderDiscountProductSelect();
                me.renderPriceProductMeta();
                me.loadAllAfterProducts();
            });
        });
    };

    DistributorPanel.prototype.loadAllAfterProducts = function () {
        // آماده‌سازی فرم‌های خرید/فروش با محصولات واقعی
        this._renderPriceSelect();
        this.renderReportProductSelect();
        this.rebuildCustomerPriceList();
    };

    // ---------------- داشبورد ----------------
    DistributorPanel.prototype.loadDashboard = function () {
        var me = this;
        apiGet('/distributors/dashboard/').then(function (res) {
            if (!res.success) {
                console.warn('dashboard', errMsg(res));
                renderPanelLoadError('companyInventoryGrid', 'بارگذاری داشبورد ناموفق بود.', function () { me.loadDashboard(); });
                return;
            }
            me.dashboard = res.data;
            me.distributor = res.data.distributor || null;
            me.renderDashboard();
            me.renderSettings();
        }).catch(function () {
            renderPanelLoadError('companyInventoryGrid', 'ارتباط با داشبورد برقرار نشد.', function () { me.loadDashboard(); });
        });
    };

    DistributorPanel.prototype.renderDashboard = function () {
        var d = this.dashboard;
        if (!d) return;

        var setTxt = function (el, txt) {
            if (el) el.textContent = txt;
        };
        setTxt($id('debtorBalance'), toman(d.debtor_balance));
        setTxt($id('todaySales'), toman(d.today_sales));
        setTxt($id('weekSales'), toman(d.week_sales));
        setTxt($id('monthSales'), toman(d.month_sales));
        setTxt($id('debtToCompanyCard'), toman(d.debt_to_company));

var openCount = (d.new_tickets || 0) + (d.ticket_answered || 0);
        setTxt($id('ticketBadge'), d.new_tickets || 0);
    };

    // ---------------- انبار (localStorage مشترک با منشی) ----------------
    DistributorPanel.prototype.renderInventory = function () {
        var inv = {};
        try {
            inv = JSON.parse(localStorage.getItem('zokInventory') || '{}') || {};
        } catch (e) {
            inv = {};
        }

        var all = [];
        ['90', '60', 'steak', 'roast'].forEach(function (cat) {
            (inv[cat] || []).forEach(function (p) {
                if (p && p.name) {
                    var pkg = Number(p.packageQty) || 0;
                    var carton = Number(p.cartonQty) || 0;
                    all.push({ name: p.name, pkg: pkg, carton: carton, total: pkg + carton });
                }
            });
        });

        var grid = $id('companyInventoryGrid');
        if (grid) {
            if (!all.length) {
                grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-gray);padding:18px;font-size:13px;">داده‌ای از انبار شرکت در دسترس نیست.</div>';
            } else {
                grid.innerHTML = all.map(function (p) {
                    return '<div class="inventory-summary-card">' +
                        '<div class="summary-product-name"><i class="fas fa-cube"></i> ' + esc(p.name) + '</div>' +
                        '<div class="summary-values">' +
                        '<div class="summary-item"><span class="summary-label">📦 بسته‌ای</span><span class="summary-value package">' + faNum(p.pkg) + '</span></div>' +
                        '<div class="summary-item"><span class="summary-label">📦 کارتنی</span><span class="summary-value carton">' + faNum(p.carton) + '</span></div>' +
                        '</div></div>';
                }).join('');
            }
        }

        var low = $id('lowStockBody');
        if (low) {
            var filtered = all.filter(function (p) { return p.total < 75; });
            if (!filtered.length) {
                low.innerHTML = '<tr><td colspan="4" style="opacity:0.6;">همه محصولات موجودی کافی دارند.</td></tr>';
            } else {
                low.innerHTML = filtered.map(function (p, i) {
                    var badge = p.total < 50
                        ? '<span class="status-badge high">در حال اتمام</span>'
                        : '<span class="status-badge medium">نزدیک به اتمام</span>';
                    return '<tr><td>' + faNum(i + 1) + '</td><td>' + esc(p.name) + '</td><td>' +
                        faNum(p.pkg) + ' بسته / ' + faNum(p.carton) + ' کارتن</td><td>' + badge + '</td></tr>';
                }).join('');
            }
        }
    };

    // ================================================================
    // خرید از شرکت
    // ================================================================
    DistributorPanel.prototype.renderPurchaseSelects = function () {
        var me = this;
        var opts = '<option value="">انتخاب محصول...</option>' + this.products.map(function (p) {
            var price = me._priceFor(p.id);
            return '<option value="' + p.id + '">' + esc(p.name) + ' − ' + faNum(price) + ' تومان</option>';
        }).join('');
        window.purchaseOpts = opts;
    };

    DistributorPanel.prototype._purchaseRow = function () {
        var me = this;
        var sel = document.createElement('select');
        sel.className = 'purchase-product-select';
        sel.style.flex = '1';
        sel.innerHTML = window.purchaseOpts || '<option value="">—</option>';

        var qty = document.createElement('input');
        qty.type = 'number';
        qty.className = 'purchase-qty';
        qty.value = '1';
        qty.min = '1';
        qty.style.width = '80px';

        var unit = document.createElement('select');
        unit.className = 'purchase-unit';
        unit.style.width = '90px';
        unit.innerHTML = '<option value="package">بسته</option><option value="carton">کارتن</option>';

        var price = document.createElement('span');
        price.className = 'product-price';

        var remove = document.createElement('button');
        remove.className = 'remove-product-btn';
        remove.style.cssText = 'background:#e74c3c;border:none;color:#fff;width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:14px;';
        remove.textContent = '×';
        remove.addEventListener('click', function () {
            wrap.parentNode.removeChild(wrap);
            me.recalcPurchase();
        });

        var wrap = document.createElement('div');
        wrap.className = 'product-select-item';
        wrap.appendChild(sel);
        wrap.appendChild(unit);
        wrap.appendChild(qty);
        wrap.appendChild(price);
        wrap.appendChild(remove);

        var refresh = function () {
            var pid = Number(sel.value);
            var u = unit.value || 'package';
            var linePrice = me._linePriceFor(pid, u);
            price.textContent = faNum(linePrice) + ' تومان' +
                (u === 'carton' ? ' (هر کارتن ' + faNum(me._packFor(pid)) + ' بسته)' : '');
            me.recalcPurchase();
        };
        sel.addEventListener('change', refresh);
        unit.addEventListener('change', refresh);
        qty.addEventListener('input', function () { me.recalcPurchase(); });
        refresh();
        return wrap;
    };

    DistributorPanel.prototype.recalcPurchase = function () {
        var total = 0;
        var rows = document.querySelectorAll('#purchaseProductsContainer .product-select-item');
        rows.forEach(function (row) {
            var qty = Number(row.querySelector('.purchase-qty').value) || 0;
            var pid = Number(row.querySelector('.purchase-product-select').value);
            var uSel = row.querySelector('.purchase-unit');
            var u = uSel ? (uSel.value || 'package') : 'package';
            total += qty * (this._linePriceFor(pid, u) || 0);
        }, this);
        var el = $id('purchaseTotalPrice');
        if (el) el.textContent = toman(total);
    };

    DistributorPanel.prototype.submitPurchase = function () {
        var me = this;
        var container = $id('purchaseProductsContainer');
        var items = [];
        var rows = container.querySelectorAll('.product-select-item');
        rows.forEach(function (row) {
            var sel = row.querySelector('.purchase-product-select');
            var pid = Number(sel.value);
            var qty = Number(row.querySelector('.purchase-qty').value) || 0;
            var unit = row.querySelector('.purchase-unit').value || 'package';
            if (pid && qty > 0) {
                var product = me.productsById[pid];
                items.push({
                    product_id: pid,
                    product_name: product ? product.name : '',
                    unit: unit,
                    quantity: qty,
                    price: me._priceFor(pid)
                });
            }
        });

        if (!items.length) {
            var mb = $id('purchaseMsg');
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('حداقل یک قلم محصول با تعداد بیشتر از صفر انتخاب کنید.', false)); }
            return;
        }

        apiPost('/distributors/purchases/', { items: items }).then(function (res) {
            var mb = $id('purchaseMsg');
            if (mb) mb.innerHTML = '';
            if (res.success) {
                $id('purchaseForm').style.display = 'none';
                if (mb) mb.appendChild(msgBox('سفارش خرید با موفقیت ثبت شد و در انتظار تایید شرکت است.', true));
                me.loadPurchases();
                me.loadDashboard();
            } else {
                if (mb) mb.appendChild(msgBox(errMsg(res), false));
            }
        });
    };

    DistributorPanel.prototype.loadPurchases = function () {
        var me = this;
        apiGet('/distributors/purchases/?page_size=100').then(function (res) {
            if (!res.success) {
                renderPanelLoadError('purchaseHistoryBody', errMsg(res), function () { me.loadPurchases(); });
                return;
            }
            me.purchases = res.data.results || res.data || [];
            me.renderPurchases();
        }).catch(function () {
            renderPanelLoadError('purchaseHistoryBody', 'بارگذاری تاریخچه خرید ناموفق بود.', function () { me.loadPurchases(); });
        });
    };

    DistributorPanel.prototype.renderPurchases = function (filterText, fromDate, toDate) {
        var me = this;
        var body = $id('purchaseHistoryBody');
        if (!body) return;

        var fText = (filterText == null ? '' : filterText).trim();
        var list = me.purchases.filter(function (p) {
            var itemsTxt = (p.items || []).map(function (i) { return i.product_name; }).join(' ');
            var okTxt = !fText || itemsTxt.indexOf(fText) !== -1;
            var okDate = true;
            if (fromDate) {
                var d = new Date(p.created_at);
                if (d.getTime() < new Date(fromDate).getTime()) okDate = false;
            }
            if (toDate && okDate) {
                var d2 = new Date(p.created_at);
                if (d2.getTime() > new Date(toDate).getTime() + 86399999) okDate = false;
            }
            return okTxt && okDate;
        });

        if (!list.length) {
            body.innerHTML = '<tr><td colspan="9" style="opacity:0.6;">سفارش خریدی یافت نشد.</td></tr>';
            return;
        }

        body.innerHTML = list.map(function (p, i) {
            var itemsTxt = (p.items || []).map(function (it) {
                return esc(it.product_name) + ' (' + faNum(it.quantity) + ' ' + (it.unit === 'carton' ? 'کارتن' : 'بسته') + ')';
            }).join('، ');
            return '<tr>' +
                '<td>' + faNum(i + 1) + '</td>' +
                '<td>#' + esc(p.id) + '</td>' +
                '<td>' + faDateTime(p.created_at) + '</td>' +
                '<td>' + itemsTxt + '</td>' +
                '<td>' + toman(p.total_amount) + '</td>' +
                '<td>—</td>' +
                '<td>—</td>' +
                '<td>' + statusBadge(p.status, PURCHASE_STATUS) + '</td>' +
                '<td><button class="btn-secondary btn-sm view-purchase-invoice" data-id="' + p.id + '">مشاهده فاکتور</button></td>' +
                '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.openPurchaseInvoice = function (id) {
        var me = this;
        var p = null;
        for (var i = 0; i < me.purchases.length; i++) {
            if (me.purchases[i].id === id) { p = me.purchases[i]; break; }
        }
        if (!p) return;
        var box = $id('purchaseInvoiceBox');
        var content = $id('purchaseInvoiceContent');
        if (!box || !content) return;

        var rows = (p.items || []).map(function (it) {
            return '<tr><td>' + esc(it.product_name) + '</td><td>' + faNum(it.quantity) + ' ' +
                (it.unit === 'carton' ? 'کارتن' : 'بسته') + '</td><td>' + toman(it.price) + '</td><td>' + toman(it.total) + '</td></tr>';
        }).join('');

        content.innerHTML =
            '<div style="padding:4px 0 12px;">' +
            '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">' +
            '<div><strong>شماره سفارش:</strong> #' + esc(p.id) + '</div>' +
            '<div><strong>تاریخ:</strong> ' + faDateTime(p.created_at) + '</div>' +
            '<div><strong>وضعیت:</strong> ' + statusBadge(p.status, PURCHASE_STATUS) + '</div>' +
            '</div>' +
            '<table class="data-table" style="min-width:520px;"><thead><tr><th>محصول</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th></tr></thead>' +
            '<tbody>' + rows + '</tbody></table>' +
            '<div style="margin-top:14px;text-align:left;font-size:16px;font-weight:700;color:var(--mustard-yellow);">جمع کل: ' + toman(p.total_amount) + '</div>' +
            '</div>';
        box.style.display = 'block';
        box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    // ================================================================
    // سفارش مشتریان (فروش)
    // ================================================================
    DistributorPanel.prototype._renderPriceSelect = function () {
        var me = this;
        var priceProducts = this.products.filter(function (p) {
            var code = (p.code || '').toString().toUpperCase();
            if (code.startsWith('HAM-') || code.startsWith('STK-') || code.startsWith('RST-')) return true;
            return false;
        });
        if (!priceProducts.length) {
            priceProducts = this.products;
        }
        var opts = '<option value="">OU+O�OrOO" U.O-O�U^U,...</option>' + priceProducts.map(function (p) {
            var base = Number(p.base_price) || 0;
            return '<option value="' + p.id + '" data-id="' + p.id + '">' + esc(p.name) + (base ? " (" + faNum(base) + ")" : "") + '</option>';
        }).join('');
        var el2 = $id('priceProductSelectModal');
        if (el2) el2.innerHTML = opts;
    };

    DistributorPanel.prototype.loadOrders = function () {
        var me = this;
        apiGet('/orders/?page_size=100').then(function (res) {
            if (!res.success) return;
            me.orders = res.data.results || res.data || [];
            me.renderOrders();
            me.renderLedgerIfOpen();
        });
    };

    DistributorPanel.prototype._customerName = function (id) {
        var c = this.custMap[id];
        if (c) return c.full_name || c.company_name || c.username || '—';
        return 'مشتری #' + id;
    };

    DistributorPanel.prototype.renderOrders = function (filterInvoice, filterName, fromDate, toDate) {
        var me = this;
        var body = $id('salesHistoryBody');
        if (!body) return;

        var fInv = (filterInvoice == null ? '' : filterInvoice).trim();
        var fName = (filterName == null ? '' : filterName).trim();

        var list = me.orders.filter(function (o) {
            var okInv = !fInv || String(o.order_number || o.id).indexOf(fInv) !== -1;
            var okName = !fName || (me._customerName(o.customer) || '').indexOf(fName) !== -1;
            var okDate = true;
            if (fromDate) {
                var d = new Date(o.created_at);
                if (d.getTime() < new Date(fromDate).getTime()) okDate = false;
            }
            if (toDate && okDate) {
                var d2 = new Date(o.created_at);
                if (d2.getTime() > new Date(toDate).getTime() + 86399999) okDate = false;
            }
            return okInv && okName && okDate;
        });

        if (!list.length) {
            body.innerHTML = '<tr><td colspan="11" style="opacity:0.6;">فاکتوری یافت نشد.</td></tr>';
            return;
        }

        body.innerHTML = list.map(function (o, i) {
            var itemsTxt = (o.items || []).map(function (it) {
                return esc(it.product_name || it.name || '') + ' (' + faNum(it.quantity) + ')';
            }).join('، ');
            var paid = orderPaid(o);
            var total = orderTotal(o);
            var remain = orderRemaining(o);
            return '<tr>' +
                '<td>' + faNum(i + 1) + '</td>' +
                '<td>' + esc(o.order_number || ('#' + o.id)) + '</td>' +
                '<td>' + esc(me._customerName(o.customer)) + '</td>' +
                '<td>' + faDateTime(o.created_at) + '</td>' +
                '<td>' + itemsTxt + '</td>' +
                '<td>' + toman(total) + '</td>' +
                '<td>' + toman(paid) + '</td>' +
                '<td>۰</td>' +
                '<td>' + toman(Math.max(remain, 0)) + '</td>' +
                '<td>' + statusBadge(o.status, ORDER_STATUS) + '</td>' +
                '<td><button class="btn-secondary btn-sm print-sale-invoice" data-id="' + o.id + '">چاپ</button></td>' +
                '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.printInvoice = function (title, headLines, items, footerLines) {
        var w = window.open('', '_blank', 'width=700,height=600');
        if (!w) return;
        var itemRows = items.map(function (it) {
            return '<tr><td>' + esc(it.name) + '</td><td>' + faNum(it.qty) + (it.unit ? ' ' + it.unit : '') + '</td><td>' + toman(it.price) + '</td><td>' + toman(it.total) + '</td></tr>';
        }).join('');
        w.document.write(
            '<html dir="rtl"><head><meta charset="utf-8"><title>' + esc(title) + '</title>' +
            '<style>body{font-family:Tahoma,Arial;padding:30px;direction:rtl;color:#222;}' +
            'h2{margin:0 0 6px;font-size:18px;} table{width:100%;border-collapse:collapse;margin-top:16px;font-size:13px;}' +
            'th,td{border:1px solid #bbb;padding:7px 10px;text-align:right;}' +
            'th{background:#f4f4f4;} .tot{margin-top:16px;text-align:left;font-size:15px;font-weight:bold;}' +
            '.muted{color:#666;font-size:12px;margin:2px 0;}</style></head><body>' +
            '<h2>' + esc(title) + '</h2>' +
            headLines.map(function (l) { return '<div class="muted">' + esc(l) + '</div>'; }).join('') +
            '<table><thead><tr><th>نام</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th></tr></thead><tbody>' + itemRows + '</tbody></table>' +
            footerLines.map(function (l) { return '<div class="tot">' + esc(l) + '</div>'; }).join('') +
            '<script>window.onload=function(){setTimeout(function(){window.print();},300);};<\/script></body></html>'
        );
        w.document.close();
    };

    DistributorPanel.prototype.openSaleInvoice = function (orderId) {
        var me = this;
        var o = null;
        for (var i = 0; i < me.orders.length; i++) {
            if (me.orders[i].id === orderId) { o = me.orders[i]; break; }
        }
        if (!o) return;
        var items = (o.items || []).map(function (it) {
            var total = (it.total != null && it.total !== '') ? Number(it.total) : Number(it.price) * Number(it.quantity);
            return {
                name: it.product_name || it.name || '',
                qty: it.quantity,
                price: it.price,
                total: isNaN(total) ? 0 : total,
                unit: it.unit === 'carton' ? 'کارتن' : 'بسته'
            };
        });
        var head = ['مشتری: ' + me._customerName(o.customer), 'شماره فاکتور: ' + (o.order_number || ('#' + o.id)), 'تاریخ: ' + faDateTime(o.created_at)];
        var foot = ['جمع کل: ' + toman(o.total_price), 'پرداخت شده: ' + toman(o.paid_amount), 'مانده حساب: ' + toman(orderRemaining(o))];
        me.printInvoice('فاکتور فروش', head, items, foot);
    };

    // ================================================================
    // مشتریان
    // ================================================================
    DistributorPanel.prototype.loadCustomers = function () {
        var me = this;
        apiGet('/distributors/customers/?page_size=200').then(function (res) {
            if (!res.success) {
                console.warn('customers', errMsg(res));
                renderPanelLoadError('customerList', errMsg(res), function () { me.loadCustomers(); });
                return;
            }
            me.customers = res.data.results || res.data || [];
            me.custMap = {};
            me.customers.forEach(function (c) { me.custMap[c.id] = c; });
            me.renderCustomerList();
            me.renderReminderCustomerSelect();
        });
    };

    DistributorPanel.prototype.renderCustomerList = function (search) {
        var me = this;
        var list = $id('customerList');
        if (!list) return;
        var q = (search || '').trim();

        var filtered = me.customers.filter(function (c) {
            if (!q) return true;
            var name = (c.full_name || c.company_name || c.username || '');
            var phone = c.phone || '';
            var nat = c.national_id || '';
            return name.indexOf(q) !== -1 || phone.indexOf(q) !== -1 || nat.indexOf(q) !== -1;
        });

        if (!filtered.length) {
            list.innerHTML = '<div class="customer-card"><div class="customer-info"><div class="name" style="opacity:0.6;">مشتری‌ای یافت نشد.</div></div></div>';
            return;
        }

        list.innerHTML = filtered.map(function (c) {
            var name = c.full_name || c.company_name || c.username || ('مشتری #' + c.id);
            var details =
                (c.phone ? '<span><i class="fas fa-phone"></i> ' + esc(c.phone) + '</span>' : '') +
                (c.email ? '<span><i class="fas fa-envelope"></i> ' + esc(c.email) + '</span>' : '') +
                '<span><i class="fas fa-shopping-cart"></i> ' + faNum(c.order_count != null ? c.order_count : 0) + ' سفارش</span>' +
                '<span><i class="fas fa-credit-card"></i> ' + toman(c.account_balance) + '</span>' +
                (c.address ? '<span><i class="fas fa-home"></i> ' + esc(c.address) + '</span>' : '');
            var badge = Number(c.account_balance) > 0
                ? '<span class="tag vip">بدهکار</span>'
                : '<span class="tag loyal">تسویه</span>';
            return '<div class="customer-card" data-customer="' + c.id + '">' +
                '<div class="customer-info"><div class="name">' + esc(name) + '</div>' +
                '<div class="detail">' + details + '</div></div>' +
                '<div class="customer-badges">' + badge + '</div>' +
                '<div style="display:flex;gap:6px;flex-wrap:wrap;">' +
                '<button class="btn-primary btn-sm view-customer" data-id="' + c.id + '">پروفایل</button>' +
                '<button class="btn-secondary btn-sm msg-customer" data-id="' + c.id + '">پیام</button>' +
                '<button class="btn-secondary btn-sm view-customer-debt" data-id="' + c.id + '">بدهی</button>' +
                '<button class="btn-secondary btn-sm set-customer-price" data-id="' + c.id + '">ثبت قیمت دستی</button>' +
                '</div></div>';
        }).join('');
    };

    DistributorPanel.prototype.saveCustomerPrices = function (customerId, map, done) {
        var me = this;
        var keys = Object.keys(map || {});
        if (!customerId || !keys.length) {
            if (done) done(true, 0);
            return;
        }
        // ذخیره همزمان همه قیمت‌ها در یک درخواست (سرور همزمان در حساب مشتری سینک می‌کند)
        var prices = keys.map(function (pid) {
            return {
                product: Number(pid),
                price: Number((map[pid] || {}).price) || 0
            };
        }).filter(function (it) { return it.product > 0 && it.price > 0; });
        if (!prices.length) {
            if (done) done(true, 0);
            return;
        }
        apiPost('/pricing/customer-prices/bulk/', {
            customer: customerId,
            prices: prices
        }).then(function (res) {
            if (res.success) {
                var n = 0;
                if (res.data) n = (Number(res.data.created) || 0) + (Number(res.data.updated) || 0);
                if (done) done(true, n || prices.length);
                return;
            }
            // fallback: تک‌تک (برای سازگاری با سرور قدیمی)
            var chain = Promise.resolve();
            var saved = 0;
            keys.forEach(function (pid) {
                chain = chain.then(function () {
                    return apiPost('/pricing/customer-prices/', {
                        customer: customerId,
                        product: Number(pid),
                        price: Number((map[pid] || {}).price) || 0
                    }).then(function (r) {
                        if (r.success) saved++;
                        return r;
                    });
                });
            });
            chain.then(function () {
                if (done) done(true, saved);
            });
        });
    };

    DistributorPanel.prototype.submitNewCustomer = function () {
        var me = this;
        var name = ($id('newCustomerName').value || '').trim();
        var username = ($id('newCustomerUsername').value || '').trim();
        var pass = $id('newCustomerPassword').value || '';
        var phone = ($id('newCustomerPhone').value || '').trim();
        var nationalId = ($id('newCustomerNationalId') ? $id('newCustomerNationalId').value : '').trim();
        var address = ($id('newCustomerAddress').value || '').trim();
        var shopName = ($id('newCustomerShopName') ? $id('newCustomerShopName').value : '').trim();
        var city = ($id('newCustomerCity') ? $id('newCustomerCity').value : '').trim();
        var postalCode = ($id('newCustomerPostalCode') ? $id('newCustomerPostalCode').value : '').trim();
        var tagSel = $id('newCustomerTag');
        var tag = tagSel ? tagSel.value : 'normal';

        var mb = $id('addCustomerMsg');
        var showErr = function (m) {
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(m, false)); }
        };
        if (!name) return showErr('نام کامل را وارد کنید.');
        if (!username) return showErr('نام کاربری را وارد کنید.');
        if (pass.length < 8) return showErr('رمز عبور باید حداقل ۸ کاراکتر باشد.');
        if (!phone) return showErr('شماره تماس را وارد کنید.');

        apiPost('/distributors/customers/', {
            username: username,
            password: pass,
            first_name: name,
            company_name: name,
            phone: phone,
            national_id: nationalId,
            address: address,
            shop_name: shopName,
            city: city,
            postal_code: postalCode,
            tag: tag
        }).then(function (res) {
            if (!res.success) {
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(errMsg(res), false)); }
                return;
            }
            var cust = res.data;
            // ذخیره قیمت‌های دستی مشخص‌شده در فرم روی سرور
            var pending = me.pendingCustomerPrices || {};
            var nPending = Object.keys(pending).length;
            me.saveCustomerPrices(cust.id, pending, function (ok, saved) {
                me.pendingCustomerPrices = {};
                $id('addCustomerForm').style.display = 'none';
                if (mb) {
                    mb.innerHTML = '';
                    var note = 'مشتری با موفقیت ایجاد شد. اکنون می‌تواند با نام کاربری و رمز عبور وارد شود.';
                    if (nPending) note += ' (' + faNum(saved) + ' قیمت دستی ثبت شد.)';
                    mb.appendChild(msgBox(note, true));
                }
                me.loadCustomers();
                me.rebuildCustomerPriceList();
            });
        });
    };

    DistributorPanel.prototype._resetCustomerUIPrices = function () {
        this.pendingCustomerPrices = {};
        this.rebuildCustomerPriceList();
    };

    DistributorPanel.prototype.rebuildCustomerPriceList = function () {
        var me = this;
        var box = $id('customerPriceGrid');
        if (!box) return;
        if (!this.productsLoaded) {
            box.innerHTML = '<div style="opacity:0.6;font-size:12px;padding:8px;">O_O� O-OU, O"OO�U_O�OO�UO U.O-O�U^U,OO�...</div>';
            return;
        }
        var priceProducts = this.products.filter(function (p) {
            var code = (p.code || '').toString().toUpperCase();
            if (code.startsWith('HAM-') || code.startsWith('STK-') || code.startsWith('RST-')) return true;
            return false;
        });
        if (!priceProducts.length) {
            priceProducts = this.products;
        }
        if (!priceProducts.length) {
            box.innerHTML = '<div style="opacity:0.6;font-size:12px;padding:8px;">محصولی وجود ندارد.</div>';
            return;
        }
        var map = this.pendingCustomerPrices || {};
        box.innerHTML = priceProducts.map(function (p) {
            var cur = map[p.id];
            var val = cur ? cur.price : '';
            var base = Number(p.base_price) || 0;
            return '<div class="price-grid-row' + (val !== '' ? ' filled' : '') + '" data-id="' + p.id + '">' +
                '<span class="price-grid-name">' + esc(p.name) + (base ? ' <small>(U_OUOU�: ' + faNum(base) + ')</small>' : '') + '</span>' +
                '<input type="number" class="price-grid-input" data-id="' + p.id + '" value="' + val + '" placeholder="U,UOU.O� O_O3O�UO (O�U^U.OU+)" min="0" />' +
                '</div>';
        }).join('');
    };

    DistributorPanel.prototype.openCustomerProfile = function (id) {
        var me = this;
        var c = this.custMap[id];
        if (!c) return;

        var box = $id('customerProfileBox');
        var content = $id('customerProfileContent');
        if (!box || !content) return;

        var tagMap = { normal: 'عادی', vip: 'VIP', loyal: 'وفادار', wholesale: 'عمده‌فروش' };
        var bal = Number(c.account_balance) || 0;
        var row = function (label, value, valClass) {
            return '<tr><td style="width:160px;color:var(--text-gray);font-size:13px;">' + label + '</td>' +
                '<td class="' + (valClass || '') + '" style="color:var(--text-light);font-size:13px;font-weight:500;">' + value + '</td></tr>';
        };
        var info =
            '<div class="table-wrap"><table class="data-table" style="min-width:480px;">' +
            '<thead><tr><th colspan="2" style="text-align:right;">👤 پروفایل مشتری — ' + esc(c.full_name || c.company_name || c.username || '—') + '</th></tr></thead><tbody>' +
            row('نام کامل', esc(c.full_name || '—')) +
            row('نام شرکت', esc(c.company_name || '—')) +
            row('نام مغازه', esc(c.shop_name || '—')) +
            row('کد مشتری', esc(c.customer_code || '—')) +
            row('شماره تماس', esc(c.phone || '—')) +
            row('کد ملی', esc(c.national_id || '—')) +
            row('ایمیل', esc(c.email || '—')) +
            row('شهر', esc(c.city || '—')) +
            row('آدرس', esc(c.address || '—')) +
            row('کد پستی', esc(c.postal_code || '—')) +
            row('برچسب', '<span class="status-badge answered">' + esc(tagMap[c.tag] || 'عادی') + '</span>') +
            row('وضعیت', c.is_active === false ? '<span class="status-badge waiting">غیرفعال</span>' : '<span class="status-badge paid">فعال</span>') +
            row('مانده حساب', bal > 0 ? '<span style="color:#e74c3c;font-weight:700;">' + toman(bal) + '</span>' : toman(0)) +
            row('تعداد سفارش', faNum(c.order_count != null ? c.order_count : 0)) +
            row('مجموع خرید', toman(c.total_purchased != null ? c.total_purchased : 0)) +
            row('عضویت از', faDate(c.created_at)) +
            '</tbody></table></div>';

        content.innerHTML = info;
        this.activeCustomerId = id;
        this.renderLedger(id);
        this.renderCustomerChecks(id);

        box.style.display = 'block';
        box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    DistributorPanel.prototype.renderLedger = function (id) {
        var me = this;
        var c = this.custMap[id];
        var balEl = $id('ledgerBalanceDisplay');
        if (balEl && c) balEl.textContent = toman(c.account_balance || 0);

        var invBody = $id('ledgerInvoicesBody');
        var prfBody = $id('ledgerProfitBody');
        if (invBody) {
            var orders = this.orders.filter(function (o) { return o.customer === id; });
            if (!orders.length) {
                invBody.innerHTML = '<tr><td colspan="6" style="opacity:0.6;">فاکتوری ثبت نشده است.</td></tr>';
            } else {
                invBody.innerHTML = orders.map(function (o) {
                    return '<tr><td>' + esc(o.order_number || ('#' + o.id)) + '</td><td>' + faDate(o.created_at) + '</td>' +
                        '<td>' + toman(o.total_price) + '</td><td>' + toman(o.paid_amount) + '</td>' +
                        '<td>' + toman(orderRemaining(o)) + '</td><td>' + statusBadge(o.status, ORDER_STATUS) + '</td></tr>';
                }).join('');
            }
        }
        if (prfBody) {
            var txns = this.transactions.filter(function (t) {
                return t.customer === id && (t.transaction_type === 'PAYMENT' || t.transaction_type === 'ORDER_DEBT');
            });
            if (!txns.length) {
                prfBody.innerHTML = '<tr><td colspan="5" style="opacity:0.6;">تراکنشی ثبت نشده است.</td></tr>';
            } else {
                prfBody.innerHTML = txns.map(function (t) {
                    var isDebt = t.transaction_type === 'ORDER_DEBT';
                    return '<tr><td>#' + t.id + '</td><td>' + faDateTime(t.created_at) + '</td>' +
                        '<td>' + (isDebt ? toman(t.amount) : '۰ تومان') + '</td>' +
                        '<td>' + (isDebt ? '۰ تومان' : toman(t.amount)) + '</td>' +
                        '<td class="tx-amount ' + (isDebt ? 'minus' : 'plus') + '">' + (isDebt ? toman(t.amount) : toman(t.amount)) + '</td></tr>';
                }).join('');
            }
        }
    };

    DistributorPanel.prototype.renderLedgerIfOpen = function () {
        if (this.activeCustomerId) this.renderLedger(this.activeCustomerId);
    };

    DistributorPanel.prototype.renderCustomerChecks = function (id) {
        var me = this;
        var body = $id('checksReceivedBody');
        if (body) {
            var list = this.checks.filter(function (c) { return c.customer === id; });
            if (!list.length) {
                body.innerHTML = '<tr><td colspan="6" style="opacity:0.6;">چکی برای این مشتری ثبت نشده است.</td></tr>';
            } else {
                body.innerHTML = list.map(function (c, i) {
                    return '<tr><td>' + faNum(i + 1) + '</td><td>' + esc(c.check_number) + '</td><td>' + toman(c.amount) + '</td>' +
                        '<td>' + faDate(c.issue_date) + '</td><td>' + faDate(c.due_date) + '</td>' +
                        '<td>' + statusBadge(c.status, CHECK_STATUS) + '</td></tr>';
                }).join('');
            }
        }
        var paidBody = $id('checksPaidBody');
        if (paidBody) {
            var paid = this.checks.filter(function (c) { return c.customer === id && c.status === 'PAID'; });
            if (!paid.length) {
                paidBody.innerHTML = '<tr><td colspan="6" style="opacity:0.6;">چک پرداخت‌شده‌ای ثبت نشده است.</td></tr>';
            } else {
                paidBody.innerHTML = paid.map(function (c, i) {
                    return '<tr><td>' + faNum(i + 1) + '</td><td>' + esc(c.check_number) + '</td><td>' + toman(c.amount) + '</td>' +
                        '<td>' + faDate(c.issue_date) + '</td><td>' + esc(c.company_name || me._customerName(c.customer)) + '</td>' +
                        '<td>' + statusBadge('PAID', CHECK_STATUS) + '</td></tr>';
                }).join('');
            }
        }
    };

    DistributorPanel.prototype.openCustomerDebt = function (id) {
        var me = this;
        var c = this.custMap[id];
        var box = $id('debtModal');
        var content = $id('debtContent');
        if (!box || !content || !c) return;

        var bal = Number(c.account_balance) || 0;
        var html = '<div class="table-wrap"><table class="data-table" style="min-width:640px;">' +
            '<thead><tr><th colspan="7" style="text-align:right;">💳 بدهی <strong>' + esc(c.full_name || c.company_name || c.username) + '</strong> — مانده کل: ' +
            '<span style="color:#e74c3c;font-weight:700;">' + toman(bal) + '</span></th></tr></thead><tbody>';

        if (bal <= 0) {
            html += '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-gray);">این مشتری مانده بدهی ندارد. 🙂</td></tr>';
            content.innerHTML = html + '</tbody></table></div>';
            box.style.display = 'flex';
            return;
        }

        var overdueInvoices = this.orders.filter(function (o) {
            return o.customer === id && orderRemaining(o) > 0;
        });

        if (!overdueInvoices.length) {
            html += '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-gray);">فاکتور معوقی یافت نشد؛ مانده از تراکنش‌های دیگر است.</td></tr>';
        } else {
            html += '<tr style="background:rgba(212,160,23,0.06);"><td style="font-weight:700;">#</td><td style="font-weight:700;">شماره فاکتور</td><td style="font-weight:700;">تاریخ</td><td style="font-weight:700;">مبلغ کل</td><td style="font-weight:700;">پرداخت شده</td><td style="font-weight:700;">مانده</td><td style="font-weight:700;">وضعیت</td></tr>';
            html += overdueInvoices.map(function (o, i) {
                var total = orderTotal(o);
                var rem = orderRemaining(o);
                var paid = Math.max(total - rem, 0);
                var invNo = o.tracking_code || o.order_number || ('#' + o.id);
                return '<tr><td>' + faNum(i + 1) + '</td><td><span dir="ltr" style="color:var(--mustard-yellow);font-weight:600;">' + esc(invNo) + '</span></td>' +
                    '<td>' + faDateTime(o.created_at) + '</td>' +
                    '<td>' + toman(total) + '</td><td class="tx-amount plus">' + toman(paid) + '</td>' +
                    '<td class="tx-amount minus">' + toman(rem) + '</td>' +
                    '<td>' + statusBadge(o.status, ORDER_STATUS) + '</td></tr>';
            }).join('');
        }
        content.innerHTML = html + '</tbody></table></div>';
        box.style.display = 'flex';
    };

    // ================================================================
    // تیکت‌ها
    // ================================================================
    DistributorPanel.prototype.loadTickets = function () {
        var me = this;
        apiGet('/tickets/open_tickets/').then(function (res) {
            if (!res.success) {
                console.warn('tickets', errMsg(res));
                renderPanelLoadError('ticketList', errMsg(res), function () { me.loadTickets(); });
                return;
            }
            me.tickets = res.data.tickets || [];
            me.renderTickets();
            var badge = $id('ticketBadge');
            if (badge) badge.textContent = String(me.tickets.length);
        });
    };

    DistributorPanel.prototype.renderTickets = function (typeFilter, statusFilter, searchName) {
        var me = this;
        var list = $id('ticketList');
        if (!list) return;

        var fType = typeFilter || 'all';
        var fStatus = statusFilter || 'all';
        var fName = (searchName || '').trim();

        var filtered = me.tickets.filter(function (t) {
            var isCustomer = t.user_role === 'CUSTOMER';
            var isSecretary = t.user_role === 'SECRETARY' || t.user_role === 'ADMIN';
            var isOwner = !isCustomer && !isSecretary;
            var typeKey = isCustomer ? 'customer' : (isSecretary ? 'secretary' : 'owner');
            var stKey = t.status === 'ANSWERED' ? 'answered' : 'unanswered';
            var name = String(t.user_name || '');

            var okType = fType === 'all' || typeKey === fType;
            var okSt = fStatus === 'all' || stKey === fStatus;
            var okName = !fName || name.indexOf(fName) !== -1;
            return okType && okSt && okName;
        });

        if (!filtered.length) {
            list.innerHTML = '<div style="opacity:0.6;padding:20px 0;">تیکتی یافت نشد.</div>';
            return;
        }

        var slotClass = function (t) {
            if (t.user_role === 'CUSTOMER') return 'from-customer';
            if (t.user_role === 'SECRETARY' || t.user_role === 'ADMIN') return 'from-secretary';
            return 'from-owner';
        };

        list.innerHTML = filtered.map(function (t) {
            var isAnswered = t.status === 'ANSWERED';
            var isOpen = t.status === 'OPEN';
            var stLabel = TICKET_STATUS[t.status] || t.status;
            var stClass = isAnswered ? 'answered' : (isOpen ? 'pending' : 'closed');
            var badge = t.status === 'CLOSED'
                ? '<span class="status-badge paid">' + stLabel + '</span>'
                : '<span class="status-badge ' + stClass + '">' + stLabel + '</span>';

            var actions = '';
            if (t.status !== 'CLOSED') {
                actions += '<button class="btn-primary btn-sm answer-ticket" data-id="' + t.id + '">پاسخ</button>';
                actions += '<button class="btn-secondary btn-sm close-ticket" data-id="' + t.id + '">بستن</button>';
            }

            return '<div class="ticket-item ' + slotClass(t) + (isAnswered ? ' answered' : ' unanswered') + '" data-ticket="' + t.id + '">' +
                '<div class="ticket-info">' +
                '<div class="ticket-title"><i class="fas fa-tag"></i> ' + esc(t.title) + ' − ' + esc(t.user_name || '') + '</div>' +
                '<div class="ticket-meta"><span><i class="fas fa-user"></i> ' + esc(t.user_role || '') + '</span>' +
                '<span><i class="fas fa-clock"></i> ' + faDateTime(t.created_at) + '</span>' +
                badge + '</div></div>' +
                '<div class="ticket-actions"><button class="btn-secondary btn-sm view-ticket" data-id="' + t.id + '">مشاهده</button>' +
                actions + '</div></div>';
        }).join('');
    };

    DistributorPanel.prototype.openTicket = function (id) {
        var me = this;
        var t = null;
        for (var i = 0; i < me.tickets.length; i++) {
            if (me.tickets[i].id === id) { t = me.tickets[i]; break; }
        }
        if (!t) return;

        var box = $id('ticketDetail');
        var title = $id('detailTitle');
        var msgs = $id('detailMessages');
        if (!box || !title || !msgs) return;

        title.textContent = t.title;
        this.activeTicketId = id;

        var messages = (t.messages || []).slice();
        // پیام اولیه اگر در messages نبود
        if (!messages.length && t.message) {
            messages = [{ sender_name: t.user_name, text: t.message, created_at: t.created_at, sender: 'CUSTOMER' }];
        }

        msgs.innerHTML = messages.map(function (m) {
            var staff = m.sender === 'STAFF';
            var cust = (!staff && m.sender !== 'GUEST');
            return '<div class="ticket-msg ' + (staff ? 'admin' : 'customer') + '">' +
                '<div class="ticket-msg-meta"><strong>' + esc(m.sender_name || '') + '</strong> − ' + faDateTime(m.created_at) + '</div>' +
                '<div class="msg-text">' + esc(m.text) + '</div>' +
                ((m.attachments && m.attachments.length)
                    ? '<div>' + m.attachments.map(function (a) {
                        return '<a href="' + esc(a.url) + '" target="_blank" style="color:var(--mustard-yellow);font-size:12px;">📎 ' + esc(a.name) + '</a>';
                    }).join(' ') + '</div>'
                    : '') +
                '</div>';
        }).join('') || '<div style="opacity:0.6;">پیامی ثبت نشده است.</div>';

        box.style.display = 'block';
        box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    DistributorPanel.prototype.openTicketReplyModal = function () {
        var el = $id('ticketReplyModal');
        if (el) el.style.display = 'flex';
        $id('replyModalText').value = '';
        var m = $id('modalReplyMsg');
        if (m) m.textContent = '';
    };

    DistributorPanel.prototype.sendTicketReply = function () {
        var me = this;
        if (!this.activeTicketId) return;
        var text = ($id('replyModalText').value || '').trim();
        if (!text) {
            var m = $id('modalReplyMsg');
            if (m) m.textContent = 'متن پاسخ را وارد کنید.';
            return;
        }
        $id('sendReplyModalBtn').disabled = true;
        apiPost('/tickets/' + this.activeTicketId + '/reply/', { reply_message: text }).then(function (res) {
            $id('sendReplyModalBtn').disabled = false;
            var m = $id('modalReplyMsg');
            if (!res.success) {
                if (m) { m.style.color = '#e74c3c'; m.textContent = errMsg(res); }
                return;
            }
            var el = $id('ticketReplyModal');
            if (el) el.style.display = 'none';
            me.loadTickets();
            me.openTicket(me.activeTicketId);
            // بستن مودال و نمایش پیام تایید
            var list = $id('ticketList');
            if (list) {
                var note = document.createElement('div');
                note.style.cssText = 'margin-top:10px;padding:10px 14px;border-radius:10px;font-size:13px;background:rgba(46,204,113,0.15);border:1px solid rgba(46,204,113,0.3);color:#fff;';
                note.textContent = 'پاسخ شما ارسال شد و تیکت دوباره در صف پاسخ شرکت قرار گرفت.';
                list.parentNode.insertBefore(note, list);
                setTimeout(function () { if (note.parentNode) note.parentNode.removeChild(note); }, 4000);
            }
        });
    };

    DistributorPanel.prototype.closeTicket = function (id) {
        var me = this;
        apiPost('/tickets/' + id + '/close/').then(function (res) {
            if (!res.success) {
                console.warn('close ticket', errMsg(res));
                return;
            }
            me.loadTickets();
        });
    };

    DistributorPanel.prototype.submitNewTicket = function () {
        var me = this;
        var submitButton = $id('submitTicketBtn');
        if (submitButton && submitButton.disabled) return;
        var title = ($id('ticketSubjectInput').value || '').trim();
        var message = ($id('ticketMessageInput').value || '').trim();
        var mb = $id('ticketFormMsg');

        if (!title) { mb.innerHTML = ''; mb.appendChild(msgBox('موضوع را وارد کنید.', false)); return; }
        if (!message) { mb.innerHTML = ''; mb.appendChild(msgBox('متن تیکت را وارد کنید.', false)); return; }

        var originalText = submitButton ? submitButton.innerHTML : '';
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال ارسال...';
        }
        var restore = function () {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        };

        apiPost('/tickets/', { title: title, message: message }).then(function (res) {
            if (!res.success) {
                restore();
                mb.innerHTML = '';
                mb.appendChild(msgBox(errMsg(res), false));
                return;
            }
            $id('ticketForm').style.display = 'none';
            mb.innerHTML = '';
            mb.appendChild(msgBox('تیکت شما با موفقیت ثبت شد و به دست مسئول مربوطه خواهد رسید.', true));
            me.loadTickets();
            restore();
        });
    };

    // ================================================================
    // چک‌ها
    // ================================================================
    DistributorPanel.prototype.loadChecks = function () {
        var me = this;
        apiGet('/finance/checks/?page_size=100').then(function (res) {
            if (!res.success) {
                console.warn('checks', errMsg(res));
                renderPanelLoadError('checksTableBody', errMsg(res), function () { me.loadChecks(); });
                return;
            }
            me.checks = res.data.results || res.data || [];
            me.renderChecks();
        });
    };

    DistributorPanel.prototype.renderChecks = function () {
        var me = this;
        var body = $id('checksTableBody');
        if (!body) return;

        var q = (this.checksQuery || '').trim();
        var list = this.checks.filter(function (c) {
            if (!q) return true;
            var nm = c.customer_name || (c.customer_info && c.customer_info.full_name) || c.company_name || '';
            var ph = c.customer_phone || '';
            var cn = c.check_number || '';
            return String(nm).indexOf(q) !== -1 || String(ph).indexOf(q) !== -1 || String(cn).indexOf(q) !== -1;
        });

        var countEl = $id('checksMsg');
        if (countEl) {
            countEl.innerHTML = q
                ? '<span style="color:var(--text-gray);font-size:12px;">🔍 ' + faNum(list.length) + ' نتیجه یافت شد.</span>'
                : '';
        }

        if (!list.length) {
            body.innerHTML = '<tr><td colspan="13" style="text-align:center;padding:20px;color:var(--text-gray);">چکی ثبت نشده است.</td></tr>';
            var pg = $id('checksPagination');
            if (pg) pg.innerHTML = '';
            return;
        }

        var per = this.checksPageSize;
        var total = list.length;
        var totalPages = Math.max(1, Math.ceil(total / per));
        if (this.checksPage > totalPages) this.checksPage = totalPages;
        if (this.checksPage < 1) this.checksPage = 1;
        var start = (this.checksPage - 1) * per;
        var pageData = list.slice(start, start + per);

        body.innerHTML = pageData.map(function (c, i) {
            var files = '—';
            if (c.image) {
                var src = /^https?:\/\//.test(c.image) ? c.image : (window.location.origin + c.image);
                files = '<a href="' + src + '" target="_blank" title="مشاهده فایل" style="color:var(--mustard-yellow);font-size:18px;text-decoration:none;">📎</a>';
            }
            return '<tr><td>' + faNum(start + i + 1) + '</td>' +
                '<td>' + esc(c.customer_name || me._customerName(c.customer) || '—') + '</td>' +
                '<td>' + esc(c.customer_phone || '—') + '</td>' +
                '<td>' + esc(c.customer_national_id || '—') + '</td>' +
                '<td>' + esc(c.check_number || '—') + '</td>' +
                '<td>' + esc(c.bank_name || '—') + '</td>' +
                '<td>' + toman(c.amount) + '</td>' +
                '<td>' + faDate(c.issue_date) + '</td>' +
                '<td>' + faDate(c.due_date) + '</td>' +
                '<td>' + files + '</td>' +
                '<td>' + statusBadge(c.status, CHECK_STATUS) + '</td>' +
                '<td>' + esc(c.registered_by_label || '—') + '</td>' +
                '<td><button class="btn-secondary btn-sm print-check" data-id="' + c.id + '">چاپ</button></td></tr>';
        }).join('');

        this.renderChecksPagination(totalPages);
    };

    DistributorPanel.prototype.renderChecksPagination = function (totalPages) {
        var me = this;
        var container = $id('checksPagination');
        if (!container) return;
        var cur = this.checksPage;
        var html = '<button class="prev-btn" ' + (cur === 1 ? 'disabled' : '') + ' data-page="' + (cur - 1) + '">قبلی</button>';
        for (var i = 1; i <= totalPages; i++) {
            html += '<button class="' + (i === cur ? 'active' : '') + '" data-page="' + i + '">' + faNum(i) + '</button>';
        }
        html += '<button class="next-btn" ' + (cur === totalPages ? 'disabled' : '') + ' data-page="' + (cur + 1) + '">بعدی</button>';
        container.innerHTML = html;
        container.querySelectorAll('button[data-page]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var page = Number(this.getAttribute('data-page'));
                if (page >= 1 && page <= totalPages && page !== cur) {
                    me.checksPage = page;
                    me.renderChecks();
                }
            });
        });
    };

    DistributorPanel.prototype.submitCheck = function () {
        var me = this;
        var submitButton = $id('saveCheckBtn');
        var name = ($id('checkName').value || '').trim();
        var phone = ($id('checkPhone').value || '').trim();
        var nationalId = ($id('checkNationalId').value || '').trim();
        var amount = ($id('checkAmount').value || '').trim();
        var receiveDate = $id('checkReceiveDate').value;
        var dueDate = $id('checkDueDate').value;

        var mb = $id('addCheckMsg');
        var showErr = function (m) {
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(m, false)); }
        };
        if (!name) return showErr('لطفاً نام و نام خانوادگی صاحب چک را وارد کنید.');
        if (!phone) return showErr('لطفاً شماره تماس را وارد کنید.');
        if (!nationalId) return showErr('لطفاً کد ملی صاحب چک را وارد کنید.');
        if (!amount || Number(amount) <= 0) return showErr('مبلغ چک باید بیشتر از صفر باشد.');
        if (!receiveDate) return showErr('لطفاً تاریخ دریافت چک را وارد کنید.');
        if (!dueDate) return showErr('لطفاً تاریخ سررسید چک را وارد کنید.');
        if (dueDate < receiveDate) return showErr('تاریخ سررسید نمی‌تواند قبل از تاریخ دریافت باشد.');

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال ذخیره...';
        }
        var finish = function () {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalText || 'ذخیره چک';
            }
        };

        var existing = null;
        for (var i = 0; i < me.customers.length; i++) {
            if (me.customers[i].phone === phone) { existing = me.customers[i]; break; }
        }

        var afterCustomer = function (custId) {
            if (!custId) { finish(); return showErr('خطا در ایجاد مشتری جدید'); }
            var fileInput = $id('checkFile');
            var imageFile = null;
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                imageFile = fileInput.files[0];
                if (!/^image\//.test(imageFile.type || '')) {
                    finish();
                    return showErr('فقط فایل تصویری (JPG / PNG / و...) مجاز است');
                }
            }
            var fd = new FormData();
            fd.append('customer', custId);
            fd.append('check_number', 'CHK-' + Date.now());
            fd.append('bank_name', 'بانک ملی');
            fd.append('amount', parseInt(amount, 10) || 0);
            fd.append('issue_date', receiveDate);
            fd.append('due_date', dueDate);
            if (imageFile) fd.append('image', imageFile);

            apiUpload('/finance/checks/', fd).then(function (res) {
                if (!res.success) {
                    finish();
                    if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(errMsg(res), false)); }
                    return;
                }
                finish();
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('چک با موفقیت ثبت شد.', true)); }
                var form = $id('addCheckForm');
                if (form) form.classList.remove('active');
                var toggleBtn = $id('showAddCheckBtn');
                if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-plus"></i> افزودن چک جدید';
                var fi = $id('checkFile');
                if (fi) fi.value = '';
                var preview = $id('checkFileList');
                if (preview) preview.innerHTML = '';
                var si = $id('checkSearchInput');
                if (si) si.value = '';
                me.checksQuery = '';
                me.checksPage = 1;
                me.loadChecks();
            });
        };

        if (existing) {
            afterCustomer(existing.id);
            return;
        }

        apiPost('/distributors/customers/', {
            username: 'cust_' + String(phone).replace(/[^A-Za-z0-9]/g, '') + '_' + Math.floor(Math.random() * 100000),
            password: 'Cust@' + (Date.now() % 1000000),
            first_name: name,
            company_name: name,
            phone: phone,
            national_id: nationalId
        }).then(function (res) {
            if (!res.success) {
                var again = null;
                for (var j = 0; j < me.customers.length; j++) {
                    if (me.customers[j].phone === phone) { again = me.customers[j]; break; }
                }
                if (again) { afterCustomer(again.id); return; }
                finish();
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(errMsg(res), false)); }
                return;
            }
            me.customers.push(res.data);
            me.custMap[res.data.id] = res.data;
            afterCustomer(res.data.id);
        });
    };

    DistributorPanel.prototype.printCheck = function (id) {
        var me = this;
        var c = null;
        for (var i = 0; i < me.checks.length; i++) {
            if (me.checks[i].id === id) { c = me.checks[i]; break; }
        }
        if (!c) return;
        var head = ['شماره چک: ' + c.check_number, 'بانک: ' + (c.bank_name || '—'), 'مشتری: ' + (c.customer_name || '')];
        var items = [{ name: 'مبلغ چک', qty: 1, price: c.amount, total: c.amount }];
        var foot = ['تاریخ دریافت: ' + faDate(c.issue_date), 'تاریخ سررسید: ' + faDate(c.due_date), 'وضعیت: ' + (CHECK_STATUS[c.status] ? CHECK_STATUS[c.status][0] : c.status)];
        me.printInvoice('چک مشتری', head, items, foot);
    };

    // ================================================================
    // مانده حساب
    // ================================================================
    DistributorPanel.prototype.loadTransactions = function () {
        var me = this;
        apiGet('/finance/transactions/?page_size=200').then(function (res) {
            if (!res.success) {
                console.warn('transactions', errMsg(res));
                return;
            }
            me.transactions = res.data.results || res.data || [];
            me.renderBalance();
            me.renderLedgerIfOpen();
        });
    };

    DistributorPanel.prototype._runningBalanceForCustomer = function (custId) {
        var me = this;
        var map = {};
        var txns = this.transactions.filter(function (t) { return t.customer === custId; });
        txns.sort(function (a, b) { return new Date(a.created_at) - new Date(b.created_at); });
        var run = 0;
        txns.forEach(function (t) {
            if (t.transaction_type === 'ORDER_DEBT') run += Number(t.amount) || 0;
            else if (t.transaction_type === 'PAYMENT' || t.transaction_type === 'RETURN') run -= Number(t.amount) || 0;
            else if (t.transaction_type === 'ADJUSTMENT') run += Number(t.amount) || 0;
            map[t.id] = run;
        });
        return map;
    };

    DistributorPanel.prototype.renderBalance = function (search, fromDate, toDate) {
        var me = this;

        var custBalEl = $id('customerDebtToDistributor');
        if (custBalEl && this.dashboard) custBalEl.textContent = toman(this.dashboard.debtor_balance);
        var coBalEl = $id('debtToCompany');
        if (coBalEl && this.dashboard) coBalEl.textContent = toman(this.dashboard.debt_to_company);

        // --- تراکنش‌های مشتریان ---
        var cBody = $id('customerBalanceBody');
        if (cBody) {
            var runMap = this._runningBalanceForCustomer(null);
            // محاسبه برای همه مشتریان
            var runningByTxn = {};
            var byCust = {};
            this.transactions.forEach(function (t) {
                if (t.customer != null) {
                    (byCust[t.customer] = byCust[t.customer] || []).push(t);
                }
            });
            Object.keys(byCust).forEach(function (cid) {
                Object.assign(runningByTxn, me._runningBalanceForCustomer(Number(cid)) || {});
            });

            var q = (search || '').trim();
            var list = this.transactions.filter(function (t) {
                if (t.customer == null) return false;
                var okName = true;
                if (q) {
                    // جستجو بر اساس نام، نام خانوادگی، شرکت، تلفن، کد مشتری و نام کاربری
                    var c = me.custMap[t.customer] || {};
                    var hay = [
                        me._customerName(t.customer),
                        c.company_name, c.shop_name, c.phone,
                        c.customer_code, c.username, c.national_id
                    ].filter(function (x) { return x; }).join(' ');
                    okName = hay.indexOf(q) !== -1;
                }
                var okDate = true;
                if (fromDate) {
                    var d = new Date(t.created_at);
                    if (d.getTime() < new Date(fromDate).getTime()) okDate = false;
                }
                if (toDate && okDate) {
                    var d2 = new Date(t.created_at);
                    if (d2.getTime() > new Date(toDate).getTime() + 86399999) okDate = false;
                }
                return okName && okDate;
            });

            // نوار خلاصه بدهکاران: اسم مشتریان بدهکار + تعداد + جمع مانده
            var sumBox = $id('customerBalanceSummary');
            if (sumBox) {
                var balByCust = {};
                list.forEach(function (t) {
                    var isDebt = t.transaction_type === 'ORDER_DEBT' || t.transaction_type === 'ADJUSTMENT';
                    var run = runningByTxn[t.id] != null ? runningByTxn[t.id]
                        : ((isDebt ? Number(t.amount) || 0 : 0) - (!isDebt ? Number(t.amount) || 0 : 0));
                    balByCust[t.customer] = run;
                });
                var debtorIds = Object.keys(balByCust).filter(function (cid) { return Number(balByCust[cid]) > 0; });
                var totalDebt = debtorIds.reduce(function (s, cid) { return s + Number(balByCust[cid] || 0); }, 0);
                if (!list.length) {
                    sumBox.innerHTML = '';
                } else if (!debtorIds.length) {
                    sumBox.innerHTML = '<div style="background:rgba(46,204,113,0.08);border:1px solid rgba(46,204,113,0.3);border-radius:10px;padding:10px 14px;font-size:13px;color:#2ecc71;">✅ بدهکاری در این بازه یافت نشد — همه تسویه هستند.</div>';
                } else {
                    var names = debtorIds.slice(0, 20).map(function (cid) { return esc(me._customerName(Number(cid))); });
                    var more = debtorIds.length > 20 ? ' و ' + faNum(debtorIds.length - 20) + ' نفر دیگر' : '';
                    sumBox.innerHTML = '<div style="background:rgba(231,76,60,0.06);border:1px solid rgba(231,76,60,0.25);border-radius:10px;padding:10px 14px;font-size:13px;line-height:2;">'
                        + '<span style="color:var(--text-gray);">مشتریان بدهکار (' + faNum(debtorIds.length) + ' نفر): </span>'
                        + '<span style="color:var(--text-light);font-weight:600;">' + names.join('، ') + more + '</span>'
                        + ' <span style="color:var(--text-gray);">• جمع مانده بدهی: </span>'
                        + '<span style="color:#e74c3c;font-weight:700;">' + toman(totalDebt) + '</span></div>';
                }
            }

            if (!list.length) {
                cBody.innerHTML = '<tr><td colspan="10" style="opacity:0.6;">تراکنشی یافت نشد.</td></tr>';
            } else {
                cBody.innerHTML = list.map(function (t, i) {
                    var isDebt = t.transaction_type === 'ORDER_DEBT' || t.transaction_type === 'ADJUSTMENT';
                    var debt = isDebt ? Number(t.amount) || 0 : 0;
                    var credit = (!isDebt) ? Number(t.amount) || 0 : 0;
                    var run = runningByTxn[t.id] != null ? runningByTxn[t.id] : (debt - credit);
                    return '<tr><td>' + faNum(i + 1) + '</td>' +
                        '<td>' + faDateTime(t.created_at) + '</td>' +
                        '<td>' + esc(me._customerName(t.customer)) + '</td>' +
                        '<td>#' + esc(t.order_id || '—') + '</td>' +
                        '<td>' + esc(t.description || '—') + '</td>' +
                        '<td class="tx-amount minus">' + (debt ? toman(debt) : '۰ تومان') + '</td>' +
                        '<td class="tx-amount plus">' + (credit ? toman(credit) : '۰ تومان') + '</td>' +
                        '<td>' + toman(run) + '</td>' +
                        '<td>' + (run > 0 ? '<span class="status-badge partial">بدهکار</span>' : '<span class="status-badge paid">تسویه</span>') + '</td>' +
                        '<td><button class="btn-secondary btn-sm">چاپ</button></td></tr>';
                }).join('');
            }
        }

        // --- تراکنش‌های شرکت (خریدها از دید شرکت) ---
        var coBody = $id('companyBalanceBody');
        if (coBody) {
            var list2 = this.purchases.slice().reverse(); // قدیمی‌تر اول
            if (!list2.length) {
                coBody.innerHTML = '<tr><td colspan="10" style="opacity:0.6;">خریدی از شرکت ثبت نشده است.</td></tr>';
            } else {
                var run2 = 0;
                coBody.innerHTML = list2.map(function (p, i) {
                    run2 += Number(p.total_amount) || 0;
                    return '<tr><td>' + faNum(i + 1) + '</td>' +
                        '<td>' + faDateTime(p.created_at) + '</td>' +
                        '<td>Zamani Burger</td>' +
                        '<td>#' + esc(p.id) + '</td>' +
                        '<td>' + esc((p.items || [])[0] ? (p.items[0].product_name + (p.items.length > 1 ? ' و ' + (p.items.length - 1) + ' قلم دیگر' : '')) : '—') + '</td>' +
                        '<td class="tx-amount minus">' + toman(p.total_amount) + '</td>' +
                        '<td>۰ تومان</td>' +
                        '<td>' + toman(run2) + '</td>' +
                        '<td>' + statusBadge(p.status, PURCHASE_STATUS) + '</td>' +
                        '<td><button class="btn-secondary btn-sm">چاپ</button></td></tr>';
                }).join('');
            }
        }
    };

    // ================================================================
    // تخفیف‌ها
    // ================================================================
    DistributorPanel.prototype.renderPriceProductMeta = function () {
        // متای قیمت محصولات (سلکت‌های قیمت دستی مشتری)
        this._renderPriceSelect();
    };

    DistributorPanel.prototype.renderDiscountProductSelect = function () {
        var el = $id('discountProduct');
        if (!el) return;
        el.innerHTML = '<option value="">انتخاب محصول...</option>' + this.products.map(function (p) {
            return '<option value="' + esc(p.name) + '">' + esc(p.name) + '</option>';
        }).join('');
    };

    DistributorPanel.prototype.loadDiscounts = function () {
        var me = this;
        apiGet('/products/discounts/?page_size=100').then(function (res) {
            if (!res.success) {
                console.warn('discounts', errMsg(res));
                renderPanelLoadError('discountsTableBody', errMsg(res), function () { me.loadDiscounts(); });
                return;
            }
            me.discounts = res.data.results || res.data || [];
            me.renderDiscounts();
        });
    };

    DistributorPanel.prototype.renderDiscounts = function () {
        var me = this;
        var body = $id('discountsTableBody');
        var countEl = $id('discountCount');
        if (!body) return;

        if (!this.discounts.length) {
            body.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-gray);padding:30px;">' +
                '<i class="fas fa-tags" style="font-size:30px;display:block;margin-bottom:10px;opacity:0.5;"></i>' +
                'هنوز هیچ تخفیفی ثبت نشده است.</td></tr>';
            var pg0 = $id('discountPagination');
            if (pg0) pg0.innerHTML = '';
            if (countEl) countEl.textContent = '۰ مورد';
            return;
        }

        var today = new Date();
        today.setHours(0, 0, 0, 0);
        var per = this.discountsPageSize;
        var total = this.discounts.length;
        var totalPages = Math.max(1, Math.ceil(total / per));
        if (this.discountsPage > totalPages) this.discountsPage = totalPages;
        if (this.discountsPage < 1) this.discountsPage = 1;
        var start = (this.discountsPage - 1) * per;
        var pageData = this.discounts.slice(start, start + per);
        if (countEl) countEl.textContent = faNum(total) + ' مورد';

        body.innerHTML = pageData.map(function (d, i) {
            var s = d.start_date ? new Date(d.start_date) : null;
            var e = d.end_date ? new Date(d.end_date) : null;
            var statusClass = 'active';
            var statusText = 'فعال';
            if (e && e < today) { statusClass = 'expired'; statusText = 'منقضی'; }
            else if (s && s > today) { statusClass = 'upcoming'; statusText = 'در انتظار شروع'; }
            if (d.is_active === false) { statusClass = 'expired'; statusText = 'غیرفعال'; }
            return '<tr><td>' + faNum(start + i + 1) + '</td>' +
                '<td><strong style="color:var(--text-light);">' + esc(d.product_name || 'همه محصولات') + '</strong></td>' +
                '<td><span class="discount-percent-cell">' + faNum(d.percent) + '٪</span></td>' +
                '<td><span class="discount-code-cell">' + esc(d.code) + '</span></td>' +
                '<td>' + esc(d.start_date || '—') + '</td>' +
                '<td>' + esc(d.end_date || '—') + '</td>' +
                '<td><span class="discount-badge ' + statusClass + '">' + statusText + '</span></td>' +
                '<td><button class="btn-danger btn-sm delete-discount" data-id="' + d.id + '" title="حذف"><i class="fas fa-trash"></i></button></td></tr>';
        }).join('');

        this.renderDiscountPagination(totalPages);
    };

    DistributorPanel.prototype.renderDiscountPagination = function (totalPages) {
        var me = this;
        var container = $id('discountPagination');
        if (!container) return;
        var cur = this.discountsPage;
        var html = '<button class="prev-btn" ' + (cur === 1 ? 'disabled' : '') + ' data-page="' + (cur - 1) + '">قبلی</button>';
        for (var i = 1; i <= totalPages; i++) {
            html += '<button class="' + (i === cur ? 'active' : '') + '" data-page="' + i + '">' + faNum(i) + '</button>';
        }
        html += '<button class="next-btn" ' + (cur === totalPages ? 'disabled' : '') + ' data-page="' + (cur + 1) + '">بعدی</button>';
        container.innerHTML = html;
        container.querySelectorAll('button[data-page]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var page = Number(this.getAttribute('data-page'));
                if (page >= 1 && page <= totalPages && page !== cur) {
                    me.discountsPage = page;
                    me.renderDiscounts();
                }
            });
        });
    };

    DistributorPanel.prototype.submitDiscount = function () {
        var me = this;
        var product = $id('discountProduct').value;
        var percent = Number($id('discountPercent').value) || 0;
        var startDate = $id('discountStartDate').value;
        var endDate = $id('discountEndDate').value;
        var code = ($id('discountCode').value || '').trim().toUpperCase();

        var mb = $id('discountFormMsg');
        var showErr = function (m) {
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(m, false)); }
        };
        if (!product) return showErr('لطفاً محصول را انتخاب کنید.');
        if (percent < 1 || percent > 100) return showErr('درصد تخفیف باید بین ۱ تا ۱۰۰ باشد.');
        if (!startDate) return showErr('لطفاً تاریخ شروع را وارد کنید.');
        if (!endDate) return showErr('لطفاً تاریخ انقضا را وارد کنید.');
        if (new Date(startDate) > new Date(endDate)) return showErr('تاریخ شروع نمی‌تواند بعد از تاریخ انقضا باشد.');
        if (!code) return showErr('لطفاً کد تخفیف را وارد کنید.');
        for (var k = 0; k < me.discounts.length; k++) {
            if (me.discounts[k].code === code) return showErr('این کد تخفیف قبلاً استفاده شده است.');
        }

        apiPost('/products/discounts/', {
            product_name: product,
            percent: percent,
            start_date: startDate,
            end_date: endDate,
            code: code
        }).then(function (res) {
            if (!res.success) {
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(errMsg(res), false)); }
                return;
            }
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('کد تخفیف با موفقیت اعمال شد.', true)); }
            me.discountsPage = 1;
            me.loadDiscounts();
            var form = $id('discountForm');
            if (form) form.style.display = 'none';
            var tb = $id('showAddDiscountBtn');
            if (tb) tb.innerHTML = '<i class="fas fa-plus"></i> تخفیف جدید';
        });
    };

    DistributorPanel.prototype.deleteDiscount = function (id) {
        var me = this;
        apiDelete('/products/discounts/' + id + '/').then(function (res) {
            if (!res.success) {
                console.warn('delete discount', errMsg(res));
                return;
            }
            me.loadDiscounts();
        });
    };

    // ================================================================
    // تنظیمات پروفایل
    // ================================================================
    DistributorPanel.prototype._distributorProfile = function () {
        var d = this.distributor || {};
        var me = this.me || {};
        return {
            full_name: d.full_name || ((me.first_name ? me.first_name + ' ' + (me.last_name || '') : '') || me.username || ''),
            email: d.email != null ? d.email : (me.email || ''),
            phone: d.phone || me.phone || '',
            city: d.city || '',
            address: d.address || ''
        };
    };

    DistributorPanel.prototype.renderSettings = function () {
        var me = this;
        var p = this._distributorProfile();
        var username = (this.me && this.me.username) || '';
        var el;
        el = $id('profileName'); if (el) el.textContent = p.full_name || '—';
        el = $id('profileEmail'); if (el) el.textContent = p.email || '—';
        el = $id('profilePhone'); if (el) el.textContent = p.phone || '—';
        el = $id('profileCity'); if (el) el.textContent = p.city || '—';
        el = $id('profileAddress'); if (el) el.textContent = p.address || '—';
        el = $id('profileUsernameCard'); if (el) el.textContent = username || '—';
        el = $id('profileFullName'); if (el) el.textContent = p.full_name || '—';
        el = $id('profileUsername'); if (el) el.textContent = username ? '@' + username : '@—';
        el = $id('profileCityLine'); if (el) el.textContent = [p.city, p.phone].filter(function (x) { return x; }).join(' • ') || '—';
        el = $id('profileAvatar');
        if (el) {
            var nm = p.full_name || username || '؟';
            el.textContent = nm.trim().charAt(0);
        }

        el = $id('editName'); if (el) el.value = p.full_name;
        el = $id('editUsername'); if (el) el.value = username;
        el = $id('editEmail'); if (el) el.value = p.email || '';
        el = $id('editPhone'); if (el) el.value = p.phone || '';
        el = $id('editCity'); if (el) el.value = p.city || '';

        var addr = $id('editAddress');
        if (addr) addr.value = p.address || '';
    };

    DistributorPanel.prototype.saveProfile = function () {
        var me = this;
        var fullName = ($id('editName').value || '').trim();
        var username = ($id('editUsername').value || '').trim();
        var email = ($id('editEmail').value || '').trim();
        var phone = ($id('editPhone').value || '').trim();
        var city = ($id('editCity').value || '').trim();
        var addr = $id('editAddress') ? ($id('editAddress').value || '').trim() : '';

        var ml = $id('profileModalResult');
        if (ml) { ml.textContent = ''; ml.style.color = '#e74c3c'; }
        if (!username) {
            if (ml) ml.textContent = 'نام کاربری نمی‌تواند خالی باشد.';
            return;
        }

        var parts = fullName.split(' ');
        var first = parts.shift() || '';
        var last = parts.join(' ');

        var ml = $id('profileModalResult');
        if (ml) ml.textContent = '';

        var done = 0;
        var totalReq = (this.distributor && this.distributor.id) ? 2 : 1;
        var lastErr = '';
        var allOk = true;

        var userDone = function (res) {
            done++;
            if (res.success && me.me) {
                me.me = Object.assign({}, me.me, res.data);
                localStorage.setItem('zamaniCurrentUser', JSON.stringify(res.data));
            } else if (!res.success) {
                allOk = false;
                lastErr = errMsg(res);
            }
            if (done >= totalReq) finalize(allOk);
        };

        var distDone = function (res) {
            done++;
            if (res.success) me.loadDashboard();
            else { allOk = false; if (!lastErr) lastErr = errMsg(res); }
            if (done >= totalReq) finalize(allOk);
        };

        var finalize = function (ok) {
            var el = $id('profileModal');
            if (ok && el) el.style.display = 'none';
            var sm = $id('settingsMsg');
            if (sm) {
                sm.innerHTML = '';
                sm.appendChild(msgBox(ok ? 'پروفایل با موفقیت به‌روزرسانی شد.' : ('خطا در ذخیره پروفایل. ' + lastErr), ok));
            }
            if (ok) me.renderSettings();
        };

        apiPatch('/accounts/me/', { first_name: first, last_name: last, username: username, email: email, phone: phone }).then(userDone);

        if (this.distributor && this.distributor.id) {
            apiPatch('/distributors/' + this.distributor.id + '/', {
                full_name: fullName,
                phone: phone,
                city: city,
                address: addr
            }).then(distDone);
        }
    };

    DistributorPanel.prototype.changePassword = function () {
        var oldP = $id('oldPassword').value || '';
        var newP = $id('newPassword').value || '';
        var conf = $id('confirmPassword').value || '';
        var ml = $id('passwordModalResult');

        if (!oldP || !newP) { ml.textContent = 'همه فیلدها را پر کنید.'; return; }
        if (newP.length < 6) { ml.textContent = 'رمز جدید باید حداقل ۶ کاراکتر باشد.'; return; }
        if (newP !== conf) { ml.textContent = 'تکرار رمز جدید مطابقت ندارد.'; return; }

        apiPost('/accounts/change-password/', { old_password: oldP, new_password: newP }).then(function (res) {
            if (!res.success) {
                ml.textContent = errMsg(res) || 'خطا در تغییر رمز.';
                ml.style.color = '#e74c3c';
                return;
            }
            ml.textContent = '';
            var el = $id('passwordModal');
            if (el) el.style.display = 'none';
            var sm = $id('settingsMsg');
            if (sm) {
                sm.innerHTML = '';
                sm.appendChild(msgBox('رمز عبور با موفقیت تغییر کرد.', true));
            }
        });
    };

    // ================================================================
    // ارتباط با مشتریان (به‌صورت واقعی: پیام از طریق تیکت)
    // ================================================================
    DistributorPanel.prototype.openCustomerMsgModal = function (id) {
        var c = this.custMap[id];
        if (!c) return;
        var elName = $id('msgCustomerName');
        var elPhone = $id('msgCustomerPhone');
        if (elName) elName.textContent = c.full_name || c.company_name || c.username;
        if (elPhone) elPhone.textContent = c.phone || '—';
        this.activeMsgCustomerId = id;
        $id('msgSubject').value = 'پیام از پخش‌کننده';
        $id('msgContent').value = '';
        $id('msgType').value = 'ticket';
        var m = $id('msgModalResult');
        if (m) m.textContent = '';
        var el = $id('customerMsgModal');
        if (el) el.style.display = 'flex';
    };

    DistributorPanel.prototype.sendCustomerMsg = function () {
        var me = this;
        var c = this.custMap[this.activeMsgCustomerId];
        if (!c) return;
        var content = ($id('msgContent').value || '').trim();
        var m = $id('msgModalResult');
        if (!content) { m.textContent = 'متن پیام را وارد کنید.'; return; }

        // ارسال پیام به مشتری فقط از مسیر تیکت ممکن است
        apiPost('/tickets/', {
            title: ($id('msgSubject').value || 'پیام از پخش‌کننده'),
            message: content
        }).then(function (res) {
            if (!res.success) {
                m.style.color = '#e74c3c';
                m.textContent = errMsg(res);
                return;
            }
            $id('customerMsgModal').style.display = 'none';
            me.loadTickets();
            var list = $id('ticketList');
            if (list) {
                var note = document.createElement('div');
                note.style.cssText = 'margin-top:10px;padding:10px 14px;border-radius:10px;font-size:13px;background:rgba(46,204,113,0.15);border:1px solid rgba(46,204,113,0.3);color:#fff;';
                note.textContent = 'پیام شما در قالب تیکت ثبت شد تا توسط شرکت به مشتری منتقل شود.';
                list.parentNode.insertBefore(note, list);
                setTimeout(function () { if (note.parentNode) note.parentNode.removeChild(note); }, 5000);
            }
        });
    };

    // ================================================================
    // ارتباط با مشتریان: پیامک تکی/گروهی + یادآوری (بک‌اند واقعی)
    // ================================================================
    DistributorPanel.prototype.renderReminderCustomerSelect = function () {
        var el = $id('reminderCustomerSelect');
        if (!el) return;
        el.innerHTML = '<option value="">انتخاب مشتری...</option>' + this.customers.map(function (c) {
            var name = c.full_name || c.company_name || c.username || ('مشتری #' + c.id);
            return '<option value="' + c.id + '">' + esc(name) + ' (' + esc(c.phone || '—') + ')</option>';
        }).join('');
    };

    DistributorPanel.prototype.loadReminders = function () {
        var me = this;
        apiGet('/reminders/').then(function (res) {
            if (!res.success) return;
            me.reminders = res.data.results || res.data || [];
            me.renderReminders();
        });
    };

    DistributorPanel.prototype.renderReminders = function () {
        var body = $id('reminderTableBody');
        if (!body) return;
        if (!this.reminders.length) {
            body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:16px;color:var(--text-gray);">یادآوری ثبت نشده است.</td></tr>';
            return;
        }
        var now = new Date().getTime();
        body.innerHTML = this.reminders.map(function (r, i) {
            var overdue = !r.is_done && r.remind_at && new Date(r.remind_at).getTime() < now;
            var badge = r.is_done
                ? '<span class="status-badge paid">انجام شده</span>'
                : (overdue
                    ? '<span class="status-badge rejected">سررسید شده</span>'
                    : '<span class="status-badge waiting">در انتظار</span>');
            var ops = r.is_done
                ? '<button class="btn-secondary btn-sm done-reminder" data-id="' + r.id + '" data-done="0">بازگشایی</button> '
                : '<button class="btn-primary btn-sm done-reminder" data-id="' + r.id + '" data-done="1">انجام شد</button> ';
            ops += '<button class="btn-danger btn-sm delete-reminder" data-id="' + r.id + '">حذف</button>';
            return '<tr><td>' + faNum(i + 1) + '</td>' +
                '<td>' + esc(r.customer_name || '—') + '</td>' +
                '<td>' + esc(r.customer_phone || '—') + '</td>' +
                '<td>' + esc(r.title || '—') + (r.message ? '<br><span style="color:var(--text-gray);font-size:11px;">' + esc(r.message) + '</span>' : '') + '</td>' +
                '<td>' + faDateTime(r.remind_at) + '</td>' +
                '<td>' + badge + '</td>' +
                '<td>' + ops + '</td></tr>';
        }).join('');
    };

    DistributorPanel.prototype.submitReminder = function () {
        var me = this;
        var custId = Number($id('reminderCustomerSelect').value) || 0;
        var title = ($id('reminderTitle').value || '').trim();
        var at = $id('reminderAt').value;
        var message = ($id('reminderMessage').value || '').trim();
        var mb = $id('reminderFormMsg');
        var showErr = function (m) { if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(m, false)); } };
        if (!custId) return showErr('لطفاً مشتری را انتخاب کنید.');
        if (!title) return showErr('لطفاً عنوان یادآوری را وارد کنید.');
        if (!at) return showErr('لطفاً زمان یادآوری را وارد کنید.');
        if (at.length === 16) at += ':00';
        apiPost('/reminders/', { customer: custId, title: title, message: message, remind_at: at }).then(function (res) {
            if (!res.success) {
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox(errMsg(res), false)); }
                return;
            }
            if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('یادآوری با موفقیت ثبت شد.', true)); }
            $id('reminderTitle').value = '';
            $id('reminderAt').value = '';
            $id('reminderMessage').value = '';
            me.loadReminders();
        });
    };

    DistributorPanel.prototype.doneReminder = function (id, done) {
        var me = this;
        apiPost('/reminders/' + id + '/' + (done ? 'done' : 'undone') + '/', {}).then(function (res) {
            if (res.success) me.loadReminders();
        });
    };

    DistributorPanel.prototype.deleteReminder = function (id) {
        var me = this;
        apiDelete('/reminders/' + id + '/').then(function (res) {
            if (res.success) me.loadReminders();
        });
    };

    DistributorPanel.prototype.sendSingleSms = function () {
        var me = this;
        var phone = ($id('singleSmsRecipient').value || '').trim();
        var subject = ($id('singleSmsSubject').value || '').trim();
        var body = ($id('singleSmsMessage').value || '').trim();
        var box = $id('singleSmsResult');
        apiPost('/sms/send/', { phone: phone, subject: subject, body: body }).then(function (res) {
            if (box) box.innerHTML = '';
            if (!res.success) {
                if (box) box.appendChild(msgBox(errMsg(res), false));
                return;
            }
            if (box) box.appendChild(msgBox('پیامک با موفقیت ثبت شد.', true));
            $id('singleSmsMessage').value = '';
            me.loadSmsHistory();
        });
    };

    DistributorPanel.prototype.sendBulkSms = function () {
        var me = this;
        var group = $id('bulkGroupSelect').value || 'all';
        var subject = ($id('bulkSmsSubject').value || '').trim();
        var body = ($id('bulkSmsMessage').value || '').trim();
        var box = $id('bulkSmsResult');
        apiPost('/sms/send_bulk/', { group: group, subject: subject, body: body }).then(function (res) {
            if (box) box.innerHTML = '';
            if (!res.success) {
                if (box) box.appendChild(msgBox(errMsg(res), false));
                return;
            }
            var n = res.data && res.data.count != null ? res.data.count : '';
            if (box) box.appendChild(msgBox('پیامک برای ' + faNum(n) + ' مخاطب ثبت شد.', true));
            $id('bulkSmsMessage').value = '';
            me.loadSmsHistory();
        });
    };

    DistributorPanel.prototype.loadSmsHistory = function () {
        var me = this;
        apiGet('/sms/?page_size=50').then(function (res) {
            if (!res.success) return;
            me.smsHistory = res.data.results || res.data || [];
            me.renderSmsHistory();
        });
    };

    DistributorPanel.prototype.renderSmsHistory = function () {
        var body = $id('smsHistoryBody');
        if (!body) return;
        if (!this.smsHistory.length) {
            body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:16px;color:var(--text-gray);">پیامکی ثبت نشده است.</td></tr>';
            return;
        }
        body.innerHTML = this.smsHistory.map(function (m, i) {
            var badge = m.status === 'sent'
                ? '<span class="status-badge paid">ارسال شده</span>'
                : (m.status === 'failed'
                    ? '<span class="status-badge rejected">ناموفق</span>'
                    : '<span class="status-badge waiting">' + esc(m.status_label || 'ثبت شد') + '</span>');
            return '<tr><td>' + faNum(i + 1) + '</td>' +
                '<td>' + esc(m.phone || '—') + '</td>' +
                '<td>' + esc(m.customer_name || '—') + '</td>' +
                '<td>' + esc(m.subject || '—') + '</td>' +
                '<td>' + esc((m.body || '').slice(0, 80)) + ((m.body || '').length > 80 ? '…' : '') + '</td>' +
                '<td>' + badge + '</td>' +
                '<td>' + faDateTime(m.created_at) + '</td></tr>';
        }).join('');
    };

    // ================================================================
    // قیمت دستی مشتری (ذخیره روی سرور + سینک با پنل مشتری)
    // ================================================================
    DistributorPanel.prototype._modalProducts = function () {
        var list = (this.products || []).filter(function (p) {
            var code = (p.code || '').toString().toUpperCase();
            return code.startsWith('HAM-') || code.startsWith('STK-') || code.startsWith('RST-');
        });
        if (!list.length) list = (this.products || []).slice();
        return list;
    };

    DistributorPanel.prototype.openSetPriceModal = function (id) {
        var c = this.custMap[id];
        if (!c) return;
        var elName = $id('priceCustomerName');
        if (elName) elName.value = c.full_name || c.company_name || c.username;
        this.activeCustPriceTarget = id;
        var m = $id('priceModalResult');
        if (m) m.textContent = '';
        var el = $id('setPriceModal');
        if (el) el.style.display = 'flex';
        this.loadModalPrices();
    };

    DistributorPanel.prototype.loadModalPrices = function () {
        var me = this;
        var cid = this.activeCustPriceTarget;
        var box = $id('modalPriceGrid');
        if (!box) return;
        if (!cid) { box.innerHTML = ''; return; }
        box.innerHTML = '<div style="opacity:0.6;font-size:12px;padding:8px;">در حال بارگذاری...</div>';
        apiGet('/pricing/customer-prices/?customer=' + cid + '&page_size=200').then(function (res) {
            var rows = [];
            if (res && res.success) rows = res.data.results || res.data || [];
            me.modalPrices = rows;
            me.modalOriginal = {};
            rows.forEach(function (r) {
                me.modalOriginal[String(r.product)] = {
                    price: Number(r.price) || 0,
                    discount: r.discount_price != null ? (Number(r.discount_price) || 0) : 0
                };
            });
            me.renderModalPrices();
        });
    };

    DistributorPanel.prototype.renderModalPrices = function () {
        var box = $id('modalPriceGrid');
        if (!box) return;
        var rows = this.modalPrices || [];
        var byPid = {};
        rows.forEach(function (r) { byPid[String(r.product)] = r; });
        var products = this._modalProducts();
        var listed = {};
        products.forEach(function (p) { listed[String(p.id)] = true; });
        rows.forEach(function (r) {
            var pid = String(r.product);
            if (!listed[pid]) {
                listed[pid] = true;
                products = products.concat([{ id: r.product, name: r.product_name, base_price: r.base_price }]);
            }
        });
        if (!products.length) {
            box.innerHTML = '<div style="opacity:0.6;font-size:12px;padding:8px;">محصولی موجود نیست.</div>';
            return;
        }
        box.innerHTML = products.map(function (p) {
            var pid = String(p.id);
            var cur = byPid[pid];
            var price = cur ? (Number(cur.price) || '') : '';
            var disc = (cur && cur.discount_price != null) ? (Number(cur.discount_price) || '') : '';
            var base = Number(p.base_price) || 0;
            var hasDisc = disc !== '' && Number(disc) > 0;
            return '<div class="price-grid-row' + ((price !== '' || hasDisc) ? ' filled' : '') + '" data-id="' + pid + '">' +
                '<span class="price-grid-name">' + esc(p.name) + (base ? ' <small>(قیمت پایه: ' + faNum(base) + ')</small>' : '') + '</span>' +
                '<input type="number" class="price-grid-input modal-price-input" data-id="' + pid + '" value="' + price + '" placeholder="قیمت" min="0" />' +
                '<label style="display:flex;align-items:center;gap:5px;font-size:12px;white-space:nowrap;color:var(--text-gray);">' +
                '<input type="checkbox" class="modal-discount-toggle" data-id="' + pid + '"' + (hasDisc ? ' checked' : '') + ' /> تخفیف</label>' +
                '<input type="number" class="price-grid-input modal-discount-input" data-id="' + pid + '" value="' + disc + '" placeholder="قیمت با تخفیف" min="0"' + (hasDisc ? '' : ' disabled') + ' />' +
                '</div>';
        }).join('');
    };

    DistributorPanel.prototype.deleteModalPrice = function (id) {
        var me = this;
        apiDelete('/pricing/customer-prices/' + id + '/').then(function (res) {
            if (res && res.success) me.loadModalPrices();
        });
    };

    DistributorPanel.prototype.saveCustPriceModal = function () {
        var me = this;
        var cid = this.activeCustPriceTarget;
        if (!cid) return;
        var m = $id('priceModalResult');
        var box = $id('modalPriceGrid');
        if (!box) return;
        var prices = [];
        var toDelete = [];
        box.querySelectorAll('.price-grid-row').forEach(function (row) {
            var pid = Number(row.getAttribute('data-id')) || 0;
            if (!pid) return;
            var priceEl = row.querySelector('.modal-price-input');
            var discEl = row.querySelector('.modal-discount-input');
            var priceVal = priceEl ? (Number(priceEl.value) || 0) : 0;
            var discVal = discEl ? (Number(discEl.value) || 0) : 0;
            if (priceVal > 0 && discVal > 0 && discVal < priceVal) {
                prices.push({ product: pid, price: priceVal, discount_price: discVal });
            } else if (priceVal > 0) {
                prices.push({ product: pid, price: priceVal });
            } else if (discVal > 0) {
                prices.push({ product: pid, price: discVal, discount_price: discVal });
            } else if (me.modalOriginal[String(pid)]) {
                toDelete.push(pid);
            }
        });
        if (!prices.length && !toDelete.length) {
            if (m) m.textContent = 'مقداری وارد نشده است.';
            return;
        }
        var savedCount = 0;
        var chain = Promise.resolve();
        if (prices.length) {
            chain = chain.then(function () {
                return apiPost('/pricing/customer-prices/bulk/', { customer: cid, prices: prices }).then(function (res) {
                    if (res && res.success) {
                        savedCount = prices.length;
                        return;
                    }
                    var c2 = Promise.resolve();
                    prices.forEach(function (it) {
                        c2 = c2.then(function () {
                            return apiPost('/pricing/customer-prices/', {
                                customer: cid,
                                product: it.product,
                                price: it.price,
                                discount_price: it.discount_price || null
                            }).then(function (r) { if (r && r.success) savedCount++; });
                        });
                    });
                    return c2;
                });
            });
        }
        toDelete.forEach(function (pid) {
            chain = chain.then(function () {
                var orig = me.modalOriginal[String(pid)];
                if (!orig || !orig.price) return;
                return apiGet('/pricing/customer-prices/?customer=' + cid + '&product=' + pid + '&page_size=5').then(function (res) {
                    var rows = (res && res.success) ? (res.data.results || res.data || []) : [];
                    var target = rows[0];
                    if (!target) return;
                    return apiDelete('/pricing/customer-prices/' + target.id + '/');
                });
            });
        });
        chain.then(function () {
            if (m) m.textContent = '';
            var sm = $id('settlementMsg');
            if (sm && savedCount) {
                sm.innerHTML = '';
                var cn = me.custMap[cid] ? (me.custMap[cid].full_name || me.custMap[cid].company_name) : 'مشتری';
                sm.appendChild(msgBox(faNum(savedCount) + ' قیمت دستی برای «' + cn + '» ثبت شد.', true));
            }
            me.loadModalPrices();
        });
    };

    // ================================================================
    // منو و UI
    // ================================================================
    DistributorPanel.prototype.showSection = function (name) {
        var me = this;
        document.querySelectorAll('.panel-section').forEach(function (sec) {
            sec.classList.toggle('active', sec.id === 'section-' + name);
        });
        document.querySelectorAll('.menu-item[data-section]').forEach(function (mi) {
            mi.classList.toggle('active', mi.getAttribute('data-section') === name);
        });

        // بستن فرم‌ها و باکس‌های باز هنگام تعویض سکشن
        ['purchaseForm', 'saleForm', 'addCustomerForm', 'ticketForm'].forEach(function (f) {
            var el = $id(f);
            if (el) el.style.display = 'none';
        });
        ['ticketDetail', 'customerProfileBox', 'purchaseInvoiceBox', 'debtorDetailBox', 'ticketHistoryDetail'].forEach(function (b) {
            var el = $id(b);
            if (el) el.style.display = 'none';
        });

        if (name === 'reports') this.renderReports();
        jalaliSync();
        if (name === 'purchase') this.renderPurchases();
        if (name === 'sales') this.renderOrders();
        if (name === 'checks') this.renderChecks();
        if (name === 'settlement') this.renderBalance();
        if (name === 'customers') this.renderCustomerList();
        if (name === 'tickets') this.renderTickets();
        if (name === 'notifications') this.loadNotifications();
        if (name === 'discounts') this.renderDiscounts();
        if (name === 'settings') this.renderSettings();
        if (name === 'dashboard') this.renderDashboard();
        if (name === 'communication') {
            me.renderReminderCustomerSelect();
            me.loadReminders();
            me.loadSmsHistory();
            var cm = $id('communicationMsg');
            if (cm) cm.innerHTML = '';
        }
    };

    // ================================================================
    // اعلان‌ها (خرید نسیه مشتریان و رویدادهای مهم)
    // ================================================================
    DistributorPanel.prototype.loadNotifications = function () {
        var me = this;
        apiGet('/notifications/?page_size=50').then(function (res) {
            if (!res.success) return;
            me.notifications = res.data.results || res.data || [];
            me.renderNotifications();
            me.renderNotifBadge();
        });
    };

    DistributorPanel.prototype.renderNotifBadge = function () {
        var el = $id('notifBadge');
        if (!el) return;
        var n = (this.notifications || []).filter(function (x) { return !x.is_read; }).length;
        el.style.display = n ? '' : 'none';
        el.textContent = faNum(n);
    };

    DistributorPanel.prototype.renderNotifications = function () {
        var box = $id('notifList');
        if (!box) return;
        var list = this.notifications || [];
        if (!list.length) {
            box.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-gray);">اعلانی وجود ندارد.</div>';
            return;
        }
        box.innerHTML = list.map(function (n) {
            return '<div class="notif-item" data-id="' + n.id + '" style="' + (n.is_read ? 'opacity:0.65;' : '') + '">' +
                '<div class="notif-text"><i class="fas fa-bell"></i><strong>' + esc(n.title || 'اعلان') + '</strong><br>' +
                '<span style="font-size:12px;">' + esc(n.message || '') + '</span><br>' +
                '<span class="notif-time">' + faDateTime(n.created_at) + '</span></div>' +
                (n.is_read ? '' : '<button class="btn-secondary btn-sm mark-notif-read" data-id="' + n.id + '">خواندم</button>') +
                '</div>';
        }).join('');
    };

    DistributorPanel.prototype.markNotificationRead = function (id) {
        var me = this;
        apiPost('/notifications/' + id + '/mark_as_read/', {}).then(function (res) {
            if (res.success) me.loadNotifications();
        });
    };

    // ================================================================
    // تقویم شمسی برای همه فیلترهای تاریخ (مثل پنل منشی)
    // ورودی اصلی دست نخورده می‌ماند (میلادی برای API) و فقط نمایش شمسی است
    // ================================================================
    var jCalFmt = null;
    try {
        jCalFmt = new Intl.DateTimeFormat('en-US-u-ca-persian', { year: 'numeric', month: 'numeric', day: 'numeric', timeZone: 'UTC' });
    } catch (e) { jCalFmt = null; }

    function jDateParts(d) {
        if (!jCalFmt) return [d.getFullYear(), d.getMonth() + 1, d.getDate()];
        var p = {};
        jCalFmt.formatToParts(d).forEach(function (x) {
            if (x.type === 'year' || x.type === 'month' || x.type === 'day') p[x.type] = Number(x.value);
        });
        return [p.year, p.month, p.day];
    }

    function jMonthTitle(jy, jm) {
        var jMonths = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
        return toFa(jy) + ' ' + (jMonths[jm - 1] || '');
    }

    function gregOfJalali(jy, jm) {
        var g = new Date(Date.UTC(jy + 621, 2, 20));
        var cur;
        for (var iter = 0; iter < 6; iter++) {
            cur = jDateParts(g);
            if (cur[0] < jy || (cur[0] === jy && cur[1] < jm)) {
                var monthsAhead = (jy - cur[0]) * 12 + (jm - cur[1]);
                if (monthsAhead > 1) {
                    g = new Date(g.getTime() + Math.round(monthsAhead * 30.44) * 86400000);
                    continue;
                }
                var guard1 = 0;
                while ((cur[0] < jy || (cur[0] === jy && cur[1] < jm)) && guard1++ < 400) {
                    g = new Date(g.getTime() + 86400000);
                    cur = jDateParts(g);
                }
            }
            var guard2 = 0;
            while ((cur[0] > jy || (cur[0] === jy && cur[1] > jm)) && guard2++ < 400) {
                g = new Date(g.getTime() - 86400000);
                cur = jDateParts(g);
            }
            break;
        }
        cur = jDateParts(g);
        var guard3 = 0;
        while (cur[2] !== 1 && guard3++ < 40) {
            g = new Date(g.getTime() - 86400000);
            cur = jDateParts(g);
        }
        return g;
    }

    function jMonthLen(jy, jm) {
        if (jm <= 6) return 31;
        var ny = jm === 12 ? jy + 1 : jy;
        var nm = jm === 12 ? 1 : jm + 1;
        return Math.round((gregOfJalali(ny, nm).getTime() - gregOfJalali(jy, jm).getTime()) / 86400000);
    }

    function jalaliEnhance() {
        document.querySelectorAll('input[type="date"]').forEach(function (inp) {
            if (inp.closest('.jdate-wrap')) return;
            var wrap = document.createElement('div');
            wrap.className = 'jdate-wrap';
            inp.parentNode.insertBefore(wrap, inp.nextSibling);
            wrap.appendChild(inp);
            inp.style.display = 'none';
            var show = document.createElement('input');
            show.type = 'text';
            show.className = 'jdate-input';
            show.readOnly = true;
            show.placeholder = 'انتخاب تاریخ شمسی';
            var calIcon = document.createElement('span');
            calIcon.className = 'jcal-icon';
            calIcon.textContent = '📅';
            var pop = document.createElement('div');
            pop.className = 'jcal-pop';
            wrap.appendChild(show);
            wrap.appendChild(calIcon);
            wrap.appendChild(pop);
            var todayJ = jDateParts(new Date());
            var state = { jy: todayJ[0], jm: todayJ[1], open: false };

            var syncDisplay = function () {
                var m = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
                if (m) {
                    var j = jDateParts(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))));
                    show.value = jMonthTitle(j[0], j[1]) + ' ' + toFa(j[2]);
                } else {
                    show.value = '';
                }
            };

            var close = function () {
                state.open = false;
                pop.classList.remove('open');
            };

            var build = function () {
                var len = jMonthLen(state.jy, state.jm);
                var firstG = gregOfJalali(state.jy, state.jm);
                var firstDow = firstG.getUTCDay();
                var firstCol = (firstDow + 1) % 7;
                var cols = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
                var cell = '';
                var i, d;
                for (i = 0; i < firstCol; i++) cell += '<span></span>';
                for (d = 1; d <= len; d++) {
                    var isToday = d === todayJ[2] && state.jy === todayJ[0] && state.jm === todayJ[1];
                    cell += '<span class="jcal-day' + (isToday ? ' today' : '') + '" data-d="' + d + '">' + toFa(d) + '</span>';
                }
                pop.innerHTML = '<div class="jcal-nav"><button type="button" class="jcal-prev">‹</button><span class="jcal-title">' + jMonthTitle(state.jy, state.jm) + '</span><button type="button" class="jcal-next">›</button></div>'
                    + '<div class="jcal-grid">' + cols.map(function (c) { return '<span class="jcal-head">' + c + '</span>'; }).join('') + cell + '</div>';
            };

            wrap.addEventListener('click', function (e) {
                var navBtn = e.target.closest('.jcal-prev, .jcal-next');
                var day = e.target.closest('.jcal-day');
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
                    var dd = Number(day.getAttribute('data-d'));
                    var base = gregOfJalali(state.jy, state.jm);
                    var sel = new Date(base.getTime() + (dd - 1) * 86400000);
                    inp.value = sel.toISOString().slice(0, 10);
                    syncDisplay();
                    close();
                    inp.dispatchEvent(new Event('change', { bubbles: true }));
                    e.stopPropagation();
                    return;
                }
                if (state.open) { close(); e.stopPropagation(); return; }
                var curM = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
                if (curM) {
                    var cj = jDateParts(new Date(Date.UTC(Number(curM[1]), Number(curM[2]) - 1, Number(curM[3]))));
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
    }

    function jalaliSync() {
        document.querySelectorAll('.jdate-wrap input[type="date"]').forEach(function (inp) {
            var show = inp.parentNode.querySelector('.jdate-input');
            if (!show) return;
            var m = String(inp.value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
            if (m) {
                var j = jDateParts(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))));
                show.value = jMonthTitle(j[0], j[1]) + ' ' + toFa(j[2]);
            } else {
                show.value = '';
            }
        });
    }

    // ================================================================
    // گزارشات (پرونده اشخاص / بدهکاران / عمومی / مالی) — مثل پنل منشی
    // ================================================================
    function toFa(v) {
        return String(v == null ? '' : v).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; });
    }

    function finStatusClass(status) {
        var map = { DELIVERED: 'delivered', CONFIRMED: 'processing', PREPARING: 'processing', SHIPPED: 'shipped', CANCELLED: 'canceled', PENDING: 'waiting', SUCCESS: 'paid', FAILED: 'canceled', PAID: 'paid' };
        return map[status] || 'waiting';
    }

    function faBucketLabel(label) {
        if (!label) return '-';
        if (/^\d{4}-\d{2}-\d{2}$/.test(label)) {
            var p = label.split('-');
            var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
            return d.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
        }
        if (/^\d{4}-\d{2}$/.test(label)) {
            var p2 = label.split('-');
            var d2 = new Date(+p2[0], +p2[1] - 1, 1);
            return d2.toLocaleDateString('fa-IR', { year: 'numeric', month: 'short' });
        }
        if (/^\d{4}$/.test(label)) {
            var d3 = new Date(+label, 0, 1);
            return d3.toLocaleDateString('fa-IR', { year: 'numeric' });
        }
        return label;
    }

    DistributorPanel.prototype.reportMsg = function (html, type) {
        var el = $id('reportMsg');
        if (!el) return;
        el.innerHTML = '';
        var box = msgBox(html, type === 'success');
        if (box) el.appendChild(box);
    };

    DistributorPanel.prototype.downloadCsv = function (filename, rows, msgId) {
        var csv = rows.map(function (r) {
            return r.map(function (cell) {
                return '"' + String(cell == null ? '' : cell).replace(/"/g, '""') + '"';
            }).join(',');
        }).join('\r\n');
        var blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 100);
        var el = $id(msgId || 'reportMsg');
        if (el) { el.innerHTML = ''; el.appendChild(msgBox('📥 فایل CSV دانلود شد.', true)); }
    };

    // گزارشات از داده واقعی
    DistributorPanel.prototype.renderReports = function () {
        this.renderReportProductSelect();
        this.loadPersonList();
        this.loadDebtorsReport('', '', this.reportState.debtorSearch || '');
        this.loadGeneralReport();
        this.loadFinancialData();
    };

    // ---------------- گزارش مالی ----------------
DistributorPanel.prototype.renderFinancialChart = function (chartData, targetId) {
        var chartEl = $id(targetId || 'financialChart');
        if (!chartEl) return;
        if (!chartData || !chartData.length) {
            chartEl.innerHTML = '<div style="width:100%;text-align:center;color:var(--text-gray);font-size:13px;padding:20px;">داده‌ای برای نمودار وجود ندارد.</div>';
            return false;
        }
        var max = 0;
        chartData.forEach(function (b) { var t = Number(b.total || 0); if (t > max) max = t; });
        var barArea = Math.max(((chartEl.clientHeight || 190) - 34), 60);
        chartEl.innerHTML = chartData.map(function (b) {
            var pct = max > 0 ? Number(b.total) / max : 0;
            return '<div class="bar-item"><div class="bar" style="height:' + Math.max(4, Math.round(pct * barArea)) + 'px;"></div><div class="bar-value">' + faNum(b.total || 0) + '</div><div class="bar-label">' + esc(faBucketLabel(b.label)) + '</div></div>';
        }).join('');
        return max;
    };

    DistributorPanel.prototype.renderFinancialInvoices = function (invoices) {
        var body = $id('financialTableBody');
        if (!body) return;
        if (!invoices || !invoices.length) {
            body.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--text-gray);">فاکتوری در این بازه یافت نشد.</td></tr>';
            return;
        }
        body.innerHTML = invoices.map(function (inv, i) {
            var receipts = inv.receipts || [];
            var receiptHtml = receipts.length
                ? receipts.map(function (r) {
                    return '<a href="' + r.url + '" target="_blank" rel="noopener" title="دانلود رسید" class="btn-secondary btn-sm" style="text-decoration:none;margin:2px;"><i class="fas fa-paperclip"></i> رسید</a>';
                }).join('')
                : '<span style="color:var(--text-gray);">---</span>';
            var invNo = inv.invoice_number || ('#' + inv.id);
            return '<tr>'
                + '<td>' + toFa(i + 1) + '</td>'
                + '<td><span dir="ltr" style="color:var(--mustard-yellow);">' + esc(invNo) + '</span></td>'
                + '<td>' + faDate(inv.date) + '</td>'
                + '<td>' + esc(inv.description || '---') + '</td>'
                + '<td>' + faNum(inv.amount) + '</td>'
                + '<td>' + faNum(inv.paid) + '</td>'
                + '<td class="' + (inv.remaining > 0 ? 'red' : 'green') + '">' + faNum(inv.remaining) + '</td>'
                + '<td>' + esc(inv.method || '---') + '</td>'
                + '<td><span class="status-badge ' + finStatusClass(inv.status) + '">' + esc(inv.status_label || inv.status) + '</span></td>'
                + '<td>' + receiptHtml + '</td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderFinancialDebtors = function (debtors) {
        var body = $id('debtorTableBody');
        if (!body) return;
        if (!debtors || !debtors.length) {
            body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-gray);">بدهکاری ثبت نشده است.</td></tr>';
            return;
        }
        body.innerHTML = debtors.map(function (d, i) {
            return '<tr>'
                + '<td>' + toFa(i + 1) + '</td>'
                + '<td>' + esc(d.name || '---') + '</td>'
                + '<td>' + esc(d.phone || '---') + '</td>'
                + '<td class="red">' + faNum(d.total_debt) + '</td>'
                + '<td>' + toFa(d.orders_count) + '</td>'
                + '<td>' + toFa(d.open_tickets) + '</td>'
                + '<td><span class="status-badge unpaid">بدهی فعال</span></td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderFinancialSettlements = function (settlements) {
        var body = $id('settlementTableBody');
        if (!body) return;
        if (!settlements || !settlements.length) {
            body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--text-gray);">تسویه‌ای ثبت نشده است.</td></tr>';
            return;
        }
        body.innerHTML = settlements.map(function (d, i) {
            var cls = d.status === 'settled' ? 'paid' : 'unpaid';
            var txt = d.status === 'settled' ? 'تسویه شده' : 'دارای مانده';
            return '<tr>'
                + '<td>' + toFa(i + 1) + '</td>'
                + '<td>' + esc(d.name || '---') + '</td>'
                + '<td>' + esc(d.city || '---') + '</td>'
                + '<td>' + faNum(d.total_amount) + '</td>'
                + '<td class="green">' + faNum(d.settled) + '</td>'
                + '<td class="' + (d.balance > 0 ? 'red' : 'green') + '">' + faNum(d.balance) + '</td>'
                + '<td>' + (d.last_settlement ? faDate(d.last_settlement) : '—') + '</td>'
                + '<td><span class="status-badge ' + cls + '">' + txt + '</span></td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderFinancialPage = function () {
        if (!this.financialData) return;
        var s = this.financialData.summary || {};
        var cardSales = $id('cardTotalSales');
        var cardDiscount = $id('cardDiscounts');
        var cardBalance = $id('cardBalanceFinancial');
        if (cardSales) cardSales.innerHTML = '<div class="label">فروش کل</div><div class="value green">' + toman(s.total_sales) + '</div>';
        if (cardDiscount) cardDiscount.innerHTML = '<div class="label">تخفیف‌ها</div><div class="value red">' + toman(s.total_discount) + '</div>';
        if (cardBalance) {
            var bal = Number(s.total_balance || 0);
            cardBalance.innerHTML = '<div class="label">مانده حساب</div><div class="value gold">' + (bal < 0 ? '−' : '') + faNum(Math.abs(bal)) + ' تومان</div>';
        }
        this.renderFinancialChart(this.financialData.chart);
        this.renderFinancialInvoices(this.financialData.invoices);
        this.renderFinancialDebtors(this.financialData.debtors);
        this.renderFinancialSettlements(this.financialData.settlements);
    };

    DistributorPanel.prototype.loadFinancialData = function () {
        var me = this;
        var st = this.financialState;
        var q = '/finance/transactions/summary/?period=' + encodeURIComponent(st.period) + '&granularity=' + encodeURIComponent(st.granularity);
        if (st.from) q += '&from_date=' + encodeURIComponent(st.from);
        if (st.to) q += '&to_date=' + encodeURIComponent(st.to);
        if (st.customerName) q += '&customer_name=' + encodeURIComponent(st.customerName);
        if (st.invoiceNumber) q += '&invoice_number=' + encodeURIComponent(st.invoiceNumber);
        apiGet(q).then(function (res) {
            var mb = $id('financialMsg');
            if (res.success && res.data) {
                me.financialData = res.data;
                me.renderFinancialPage();
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('✅ گزارش مالی به‌روزرسانی شد.', true)); }
            } else {
                if (mb) { mb.innerHTML = ''; mb.appendChild(msgBox('⚠️ خطا در دریافت گزارش مالی.', false)); }
            }
        });
    };

    DistributorPanel.prototype.exportFinancialCsv = function () {
        var invoices = (this.financialData && this.financialData.invoices) || [];
        var rows = [['#', 'شماره فاکتور', 'تاریخ', 'شرح', 'مبلغ کل', 'پرداخت شده', 'مانده', 'روش پرداخت', 'وضعیت']];
        invoices.forEach(function (inv) {
            rows.push([inv.id, inv.invoice_number || ('#' + inv.id), inv.date, inv.description, inv.amount, inv.paid, inv.remaining, inv.method, inv.status_label || inv.status]);
        });
        this.downloadCsv('financial-report.csv', rows, 'financialMsg');
    };

    // ---------------- پرونده اشخاص ----------------
    DistributorPanel.prototype.loadPersonList = function () {
        this.reportState.customers = this.customers.slice();
        this.renderPersonList(this.reportState.customers);
    };

    DistributorPanel.prototype.searchPeople = function (q) {
        var query = (q || '').trim();
        if (!query) {
            this.renderPersonList(this.reportState.customers);
            return;
        }
        var list = this.reportState.customers.filter(function (c) {
            return (c.full_name || c.company_name || c.username || '').indexOf(query) !== -1 ||
                (c.phone || '').indexOf(query) !== -1 || (c.national_id || '').indexOf(query) !== -1;
        });
        this.renderPersonList(list);
    };

    DistributorPanel.prototype.renderPersonList = function (list) {
        var container = $id('personList');
        if (!container) return;
        if (!list.length) {
            container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-gray);"><i class="fas fa-user-slash" style="font-size:40px;display:block;margin-bottom:12px;"></i>شخصی یافت نشد.</div>';
            return;
        }
        container.innerHTML = list.map(function (c) {
            return '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;margin-bottom:8px;">'
                + '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
                + '<i class="fas fa-user-circle" style="font-size:26px;color:var(--mustard-yellow);"></i>'
                + '<div><strong style="color:var(--text-light);display:block;">' + esc(c.full_name || c.company_name || c.username || '—') + '</strong>'
                + '<span style="color:var(--text-gray);font-size:12px;">' + esc(c.phone || '—') + (c.national_id ? ' • کد ملی: ' + esc(c.national_id) : '') + '</span></div>'
                + '</div>'
                + '<div><button class="btn-primary btn-sm view-person-report" data-id="' + c.id + '"><i class="fas fa-folder-open"></i> مشاهده پرونده</button></div>'
                + '</div>';
        }).join('');
    };

    DistributorPanel.prototype.renderPersonInfo = function (info) {
        var bal = Number(info.account_balance || 0);
        var fields = [
            ['نام کامل', esc(info.name || '—')],
            ['نام مغازه', esc(info.shop_name || '—')],
            ['کد مشتری', toFa(info.customer_code || '—')],
            ['شماره تماس', toFa(info.phone || '—')],
            ['ایمیل', esc(info.email || '—')],
            ['کد ملی', toFa(info.national_id || '—')],
            ['کد پستی', toFa(info.postal_code || '—')],
            ['آدرس', esc(info.address || '—')],
            ['شهر', esc(info.city || '—')],
            ['پخش‌کننده', esc(info.distributor_name || '—')],
            ['مانده حساب', '<span style="color:' + (bal < 0 ? '#e74c3c' : '#2ecc71') + ';font-weight:600;">' + toman(bal) + '</span>'],
            ['تعداد کل سفارشات', toFa(info.total_orders)],
            ['مجموع مبلغ خرید', '<span style="color:var(--mustard-yellow);">' + toman(info.total_spent) + '</span>'],
            ['امتیاز', toFa(info.points)],
            ['تاریخ عضویت', toFa(info.created_at || '—')]
        ];
        return '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;">'
            + fields.map(function (f) {
                return '<div class="profile-field"><span class="field-label">' + f[0] + '</span><span class="field-value">' + f[1] + '</span></div>';
            }).join('') + '</div>';
    };

    DistributorPanel.prototype.renderPersonPurchases = function (purchases) {
        var body = $id('purchasesBody');
        if (!body) return;
        if (!purchases.length) {
            body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:25px;color:var(--text-gray);">خریدی ثبت نشده است.</td></tr>';
            return;
        }
        body.innerHTML = purchases.map(function (p) {
            return '<tr>'
                + '<td>' + toFa(p.invoice_number) + '</td>'
                + '<td>' + faDate(p.date) + '</td>'
                + '<td>' + toFa(p.items_count) + ' قلم</td>'
                + '<td>' + faNum(p.total_price) + '</td>'
                + '<td>' + statusBadge(p.status, ORDER_STATUS) + '</td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderPersonItems = function (from, to) {
        var body = $id('itemsBody');
        if (!body) return;
        var items = ((this.reportState.person && this.reportState.person.items) || []).slice();
        if (from) items = items.filter(function (it) { return String(it.date || '') >= from; });
        if (to) items = items.filter(function (it) { return String(it.date || '') <= to; });
        if (!items.length) {
            body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:25px;color:var(--text-gray);">قلمی ثبت نشده است.</td></tr>';
            return;
        }
        body.innerHTML = items.map(function (it) {
            return '<tr>'
                + '<td>' + toFa(it.invoice_number) + '</td>'
                + '<td>' + esc(it.product_name || '—') + '</td>'
                + '<td>' + toFa(it.quantity) + '</td>'
                + '<td>' + faNum(it.price) + '</td>'
                + '<td>' + faNum(it.total) + '</td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderPersonInvoices = function (invoices) {
        var body = $id('personInvoicesBody');
        if (!body) return;
        var invQ = (($id('personInvoiceSearch') || {}).value || '').trim();
        var prodQ = (($id('personProductSearch') || {}).value || '').trim();
        var rows = (invoices || []).slice();
        if (invQ) rows = rows.filter(function (inv) { return String(inv.invoice_number || '').indexOf(invQ) !== -1; });
        if (prodQ) rows = rows.filter(function (inv) {
            return (inv.products || []).some(function (p) { return String(p.name || '').indexOf(prodQ) !== -1; });
        });
        if (!rows.length) {
            body.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:25px;color:var(--text-gray);">فاکتوری یافت نشد.</td></tr>';
            return;
        }
        body.innerHTML = rows.map(function (inv, i) {
            var prods = (inv.products || []).map(function (p) {
                return esc(p.name || '') + (p.quantity ? ' <span style="color:var(--text-gray);font-size:11px;">' + toFa(p.quantity) + ' عدد</span>' : '');
            }).join('<br>');
            return '<tr>'
                + '<td>' + toFa(i + 1) + '</td>'
                + '<td>' + toFa(inv.invoice_number) + '</td>'
                + '<td style="min-width:170px;">' + (prods || '—') + '</td>'
                + '<td>' + faDate(inv.date) + '</td>'
                + '<td>' + faNum(inv.amount) + '</td>'
                + '<td class="green">' + faNum(inv.paid) + '</td>'
                + '<td class="' + (Number(inv.remaining || 0) > 0 ? 'red' : 'green') + '">' + faNum(inv.remaining) + '</td>'
                + '<td>' + esc(inv.method || '---') + '</td>'
                + '<td>' + statusBadge(inv.status, ORDER_STATUS) + '</td>'
                + '<td><button class="btn-secondary btn-sm print-sale-invoice" data-id="' + inv.id + '"><i class="fas fa-print"></i> چاپ</button></td>'
                + '</tr>';
        }).join('');
    };

    DistributorPanel.prototype.renderPersonChecks = function (checks) {
        var rec = $id('personChecksReceived');
        var paid = $id('personChecksPaid');
        if (rec) {
            if (!checks.length) {
                rec.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-gray);">چکی ثبت نشده است.</td></tr>';
            } else {
                rec.innerHTML = checks.map(function (ch, i) {
                    return '<tr>'
                        + '<td>' + toFa(i + 1) + '</td>'
                        + '<td>' + esc(ch.check_number || '---') + '</td>'
                        + '<td>' + faNum(ch.amount) + '</td>'
                        + '<td>' + faDate(ch.issue_date) + '</td>'
                        + '<td>' + faDate(ch.due_date) + '</td>'
                        + '<td>' + statusBadge(ch.status, CHECK_STATUS) + '</td>'
                        + '</tr>';
                }).join('');
            }
        }
        if (paid) {
            paid.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-gray);">چک پرداختی برای این شخص ثبت نشده است.</td></tr>';
        }
    };

    DistributorPanel.prototype.loadPersonDetail = function (customerId, fromDate, toDate) {
        var me = this;
        if (!customerId) return;
        var q = '/reports/person/?customer_id=' + encodeURIComponent(customerId);
        if (fromDate) q += '&from_date=' + encodeURIComponent(fromDate);
        if (toDate) q += '&to_date=' + encodeURIComponent(toDate);
        apiGet(q).then(function (res) {
            if (res.success && res.data) {
                me.reportState.person = res.data;
                me.reportState.personId = customerId;
                var info = res.data.info || {};
                var title = $id('personDetailTitle');
                if (title) title.innerHTML = '<i class="fas fa-folder-open" style="color:var(--mustard-yellow);"></i> پرونده کامل - ' + esc(info.name || '');
                var infoBox = $id('personInfoContent');
                if (infoBox) infoBox.innerHTML = me.renderPersonInfo(info);
                me.renderPersonPurchases(res.data.purchases || []);
                me.renderPersonItems($id('itemsFromDate').value, $id('itemsToDate').value);
                me.renderPersonInvoices(res.data.invoices || []);
                me.renderPersonChecks(res.data.checks || []);
                var box = $id('personDetailBox');
                if (box) {
                    box.classList.remove('active');
                    box.classList.add('active');
                }
                me.reportMsg('✅ پرونده شخص بارگذاری شد.', 'success');
            } else {
                me.reportMsg('⚠️ خطا در دریافت پرونده شخص.', 'error');
            }
        });
    };

    DistributorPanel.prototype.reloadPersonForActiveTab = function () {
        var activeTab = document.querySelector('.person-sub-content.active');
        var from = '', to = '';
        if (activeTab) {
            var inputs = activeTab.querySelectorAll('input[type="date"]');
            if (inputs[0]) from = inputs[0].value;
            if (inputs[1]) to = inputs[1].value;
        }
        this.loadPersonDetail(this.reportState.personId, from, to);
    };

    // ---------------- لیست بدهکاران ----------------
    DistributorPanel.prototype.loadDebtorsReport = function (fromDate, toDate, searchText) {
        var me = this;
        var el = $id('debtorList');
        if (el) el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-gray);"><i class="fas fa-spinner fa-spin" style="font-size:40px;display:block;margin-bottom:12px;"></i>در حال بارگذاری...</div>';
        var params = [];
        if (fromDate) params.push('from_date=' + encodeURIComponent(fromDate));
        if (toDate) params.push('to_date=' + encodeURIComponent(toDate));
        me.reportState.debtorSearch = searchText || '';
        if (me.reportState.debtorSearch) params.push('search=' + encodeURIComponent(me.reportState.debtorSearch));
        var q = '/reports/debtors/' + (params.length ? '?' + params.join('&') : '');
        apiGet(q).then(function (res) {
            if (res.success && res.data) {
                me.reportState.debtors = res.data.debtors || [];
                me.reportState.debtorPage = 1;
                me.renderDebtorsReport(res.data);
                me.reportMsg('✅ گزارش بدهکاران به‌روزرسانی شد.', 'success');
            } else {
                me.reportState.debtors = [];
                me.renderDebtorsReport(null);
                me.reportMsg('⚠️ خطا در دریافت گزارش بدهکاران.', 'error');
            }
        });
    };

    DistributorPanel.prototype.renderDebtorPagination = function () {
        var pageSize = 15;
        var total = this.reportState.debtors.length;
        var pages = Math.max(1, Math.ceil(total / pageSize));
        var page = this.reportState.debtorPage;
        if (page > pages) page = pages;
        if (page < 1) page = 1;
        this.reportState.debtorPage = page;
        var el = $id('debtorPagination');
        if (!el) return;
        var html = '';
        if (pages > 1) {
            html += '<button class="prev-btn" data-page="' + (page > 1 ? page - 1 : 1) + '">قبلی</button>';
            for (var i = 1; i <= pages; i++) {
                html += '<button class="' + (i === page ? 'active' : '') + '" data-page="' + i + '">' + toFa(i) + '</button>';
            }
            html += '<button class="next-btn" data-page="' + (page < pages ? page + 1 : pages) + '">بعدی</button>';
        }
        html += '<span class="pagination-info">' + toFa(total) + ' بدهکار</span>';
        el.innerHTML = html;
    };

    DistributorPanel.prototype.renderDebtorsReport = function (data) {
        var el = $id('debtorList');
        if (!el) return;
        var totalCount = data ? Number(data.total_debtors || 0) : 0;
        var totalAmount = data ? Number(data.total_debt_amount || 0) : 0;
        var html = '<div class="info-grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-bottom:16px;">'
            + '<div class="info-card" style="margin:0;"><div class="label">تعداد بدهکاران</div><div class="value red">' + toFa(totalCount) + ' نفر</div></div>'
            + '<div class="info-card" style="margin:0;"><div class="label">مجموع بدهی</div><div class="value red">' + toman(totalAmount) + '</div></div>'
            + '</div>';
        if (!this.reportState.debtors.length) {
            html += '<div style="text-align:center;padding:40px;color:var(--text-gray);">بدهکاری ثبت نشده است.</div>';
        } else {
            var pageSize = 15;
            var total = this.reportState.debtors.length;
            var pages = Math.max(1, Math.ceil(total / pageSize));
            var page = this.reportState.debtorPage;
            if (page > pages) page = pages;
            if (page < 1) page = 1;
            this.reportState.debtorPage = page;
            var start = (page - 1) * pageSize;
            var slice = this.reportState.debtors.slice(start, start + pageSize);
            html += slice.map(function (d) {
                return '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px 16px;background:rgba(255,255,255,0.03);border:1px solid rgba(231,76,60,0.25);border-radius:10px;margin-bottom:8px;">'
                    + '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
                    + '<i class="fas fa-user-tag" style="font-size:26px;color:#e74c3c;"></i>'
                    + '<div><strong style="color:var(--text-light);display:block;">' + esc(d.name || '—') + '</strong>'
                    + '<span style="color:var(--text-gray);font-size:12px;">' + esc(d.phone || '—') + ' • بدهی: <span style="color:#e74c3c;font-weight:600;">' + toman(d.total_debt) + '</span>' + (d.open_tickets ? ' • تیکت باز: ' + toFa(d.open_tickets) : '') + '</span></div>'
                    + '</div>'
                    + '<button class="btn-secondary btn-sm view-debtor" data-id="' + d.id + '"><i class="fas fa-search-dollar"></i> جزئیات حسابداری</button>'
                    + '</div>';
            }).join('');
            this.renderDebtorPagination();
        }
        el.innerHTML = html;
    };

    DistributorPanel.prototype.openDebtorDetail = function (id) {
        var debtor = null;
        for (var i = 0; i < this.reportState.debtors.length; i++) {
            if (String(this.reportState.debtors[i].id) === String(id)) { debtor = this.reportState.debtors[i]; break; }
        }
        if (!debtor) return;
        var title = $id('debtorDetailTitle');
        if (title) title.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#e74c3c;"></i> جزئیات حسابداری - ' + esc(debtor.name || '');
        var checksHtml = '';
        if ((debtor.checks || []).length) {
            checksHtml = '<div style="background:rgba(255,255,255,0.03);padding:10px 14px;border-radius:10px;margin-top:8px;"><span style="color:var(--text-gray);">چک‌های نقد نشده: </span><span style="color:var(--mustard-yellow);font-weight:600;">' + toman(debtor.total_checks) + '</span></div>';
        }
        var infoBox = $id('debtorInfoContent');
        if (infoBox) {
            infoBox.innerHTML = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;background:rgba(231,76,60,0.05);padding:14px;border-radius:10px;border:1px solid rgba(231,76,60,0.2);">'
                + '<div><span style="color:var(--text-gray);">نام:</span> <span style="color:var(--text-light);font-weight:600;">' + esc(debtor.name || '—') + '</span></div>'
                + '<div><span style="color:var(--text-gray);">شماره تماس:</span> <span style="color:var(--text-light);">' + esc(debtor.phone || '—') + '</span></div>'
                + '<div><span style="color:var(--text-gray);">کد ملی:</span> <span style="color:var(--text-light);">' + esc(debtor.national_id || '—') + '</span></div>'
                + '<div><span style="color:var(--text-gray);">تعداد سفارشات:</span> <span style="color:var(--text-light);">' + toFa(debtor.orders_count) + '</span></div>'
                + '<div><span style="color:var(--text-gray);">تیکت‌های باز:</span> <span style="color:var(--text-light);">' + toFa(debtor.open_tickets) + '</span></div>'
                + '<div><span style="color:var(--text-gray);">مجموع بدهی:</span> <span style="color:#e74c3c;font-size:20px;font-weight:700;">' + toman(debtor.total_debt) + '</span></div>'
                + '</div>' + checksHtml;
        }
        var invBody = $id('debtorInvoicesBody');
        if (invBody) {
            if (!(debtor.invoices || []).length) {
                invBody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-gray);">فاکتور معوقی در این بازه یافت نشد.</td></tr>';
            } else {
                invBody.innerHTML = debtor.invoices.map(function (inv) {
                    return '<tr>'
                        + '<td>' + toFa(inv.invoice_number) + '</td>'
                        + '<td>' + faDate(inv.date) + '</td>'
                        + '<td>' + faNum(inv.amount) + '</td>'
                        + '<td>' + faNum(inv.paid) + '</td>'
                        + '<td class="red">' + faNum(inv.remaining) + '</td>'
                        + '<td>' + esc(inv.method || '---') + '</td>'
                        + '<td>' + statusBadge(inv.status, ORDER_STATUS) + '</td>'
                        + '</tr>';
                }).join('');
            }
        }
        var box = $id('debtorDetailBox');
        if (box) {
            box.classList.remove('active');
            box.classList.add('active');
        }
    };

    // ---------------- گزارش عمومی ----------------
    DistributorPanel.prototype.renderReportProductSelect = function () {
        var sel = $id('reportProductFilter');
        if (!sel) return;
        var current = sel.value;
        sel.innerHTML = '<option value="all">همه کالاها</option>' + this.products.map(function (p) {
            return '<option value="' + p.id + '">' + esc(p.name || ('محصول #' + p.id)) + '</option>';
        }).join('');
        if (current) sel.value = current;
    };

    DistributorPanel.prototype.loadGeneralReport = function () {
        var me = this;
        var from = ($id('reportFromDate') || {}).value || '';
        var to = ($id('reportToDate') || {}).value || '';
        var product = ($id('reportProductFilter') || {}).value || 'all';
        var invNum = (($id('reportInvoiceNumber') || {}).value || '').trim();
        var saleType = ($id('reportSaleType') || {}).value || 'all';
        if (from && to && from > to) {
            me.reportMsg('⚠️ تاریخ شروع نباید از تاریخ پایان بزرگتر باشد.', 'error');
            return;
        }
        var body = $id('reportSalesTable') ? $id('reportSalesTable').querySelector('tbody') : null;
        if (body) body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:25px;color:var(--text-gray);"><i class="fas fa-spinner fa-spin"></i> در حال بارگذاری...</td></tr>';
        var params = [];
        if (from) params.push('from_date=' + encodeURIComponent(from));
        if (to) params.push('to_date=' + encodeURIComponent(to));
        if (product && product !== 'all') params.push('product_id=' + encodeURIComponent(product));
        if (invNum) params.push('invoice_number=' + encodeURIComponent(invNum));
        if (saleType && saleType !== 'all') params.push('sale_type=' + encodeURIComponent(saleType));
        apiGet('/reports/invoices/' + (params.length ? '?' + params.join('&') : '')).then(function (res) {
            var rows = (res.success && Array.isArray(res.data)) ? res.data : [];
            me.reportState.generalRows = rows;
            me.renderGeneralReport(rows);
            if (!res.success) me.reportMsg('⚠️ خطا در دریافت گزارش عمومی.', 'error');
        });
    };

    DistributorPanel.prototype.renderGeneralReport = function (rows) {
        var me = this;
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        var startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - ((today.getDay() + 6) % 7));

        var daily = 0, weekly = 0, monthly = 0, yearly = 0;
        rows.forEach(function (r) {
            var amt = Number(r.amount || 0);
            var d = new Date(String(r.date));
            if (String(r.date) === isoDate(today)) daily += amt;
            if (d.getTime() >= startOfWeek.getTime()) weekly += amt;
            if (d.getFullYear() === today.getFullYear() && d.getMonth() === today.getMonth()) monthly += amt;
            if (d.getFullYear() === today.getFullYear()) yearly += amt;
        });

        var setCard = function (id, val, label) {
            var el = $id(id);
            if (el) el.innerHTML = '<div class="label">' + label + '</div><div class="value gold">' + toman(val) + '</div>';
        };
        setCard('reportDailySales', daily, 'فروش روزانه');
        setCard('reportWeeklySales', weekly, 'فروش هفتگی');
        setCard('reportMonthlySales', monthly, 'فروش ماهانه');
        setCard('reportYearlySales', yearly, 'فروش سالانه');

        var saleBody = $id('reportSalesTable') ? $id('reportSalesTable').querySelector('tbody') : null;
        if (saleBody) {
            if (!rows.length) {
                saleBody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:25px;color:var(--text-gray);">فاکتوری با این فیلترها یافت نشد.</td></tr>';
            } else {
                saleBody.innerHTML = rows.map(function (r, i) {
                    return '<tr><td>' + toFa(i + 1) + '</td>' +
                        '<td>' + toFa(r.invoice_number) + '</td>' +
                        '<td>' + esc(r.customer_name || '—') + '</td>' +
                        '<td>' + faDate(r.date) + '</td>' +
                        '<td>' + faNum(r.amount) + '</td>' +
                        '<td class="' + (Number(r.remaining || 0) > 0 ? 'red' : 'green') + '">' + faNum(r.remaining) + '</td>' +
                        '<td>' + statusBadge(r.status, ORDER_STATUS) + '</td>' +
                        '<td><button class="btn-secondary btn-sm print-sale-invoice" data-id="' + r.id + '">چاپ</button></td></tr>';
                }).join('');
            }
        }

        var purBody = $id('purchaseReportBody');
        if (purBody) {
            if (!me.purchases.length) {
                purBody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-gray);">خریدی از شرکت ثبت نشده است.</td></tr>';
            } else {
                purBody.innerHTML = me.purchases.map(function (p, i) {
                    return '<tr><td>' + toFa(i + 1) + '</td>' +
                        '<td>#' + esc(p.id) + '</td>' +
                        '<td>' + faDateTime(p.created_at) + '</td>' +
                        '<td>' + toman(p.total_amount) + '</td>' +
                        '<td>—</td>' +
                        '<td>' + statusBadge(p.status, PURCHASE_STATUS) + '</td>' +
                        '<td><button class="btn-secondary btn-sm view-purchase-invoice" data-id="' + p.id + '">چاپ</button></td></tr>';
                }).join('');
            }
        }
    };

    DistributorPanel.prototype.exportGeneralCsv = function () {
        var rows = [['شماره', 'تاریخ', 'مشتری', 'مبلغ فاکتور', 'پرداخت شده', 'مانده', 'نوع پرداخت', 'وضعیت']];
        this.reportState.generalRows.forEach(function (r) {
            rows.push([r.invoice_number, r.date, r.customer_name, r.amount, r.paid, r.remaining, r.method, r.status]);
        });
        if (!this.reportState.generalRows.length) {
            this.reportMsg('⚠️ گزارشی برای خروجی وجود ندارد.', 'warning');
            return;
        }
        this.downloadCsv('general-report.csv', rows, 'reportMsg');
    };

    // ================================================================
    // اتصال رویدادها
    // ================================================================
    DistributorPanel.prototype.bindings = function () {
        var me = this;

        // منو
        document.querySelectorAll('.menu-item[data-section]').forEach(function (mi) {
            mi.addEventListener('click', function () {
                me.showSection(mi.getAttribute('data-section'));
            });
        });

        // خروج
        var lo = $id('logoutBtn');
        if (lo) {
            lo.addEventListener('click', function () {
                if (typeof logout === 'function') { logout(); } else {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('zamaniCurrentUser');
                    localStorage.removeItem('zamaniUserLoggedIn');
                    window.location.href = 'log.html';
                }
            });
        }

        // ---------- خرید ----------
        var nb = $id('newPurchaseBtn');
        if (nb) {
            nb.addEventListener('click', function () {
                var form = $id('purchaseForm');
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
                if (form.style.display === 'block') {
                    document.querySelector('#purchaseProductsContainer').innerHTML = '';
                    document.querySelector('#purchaseProductsContainer').appendChild(me._purchaseRow());
                    me.recalcPurchase();
                    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        }
        var addP = $id('addPurchaseProductBtn');
        if (addP) addP.addEventListener('click', function () {
            document.querySelector('#purchaseProductsContainer').appendChild(me._purchaseRow());
            me.recalcPurchase();
        });
        var subP = $id('submitPurchaseBtn');
        if (subP) subP.addEventListener('click', function () { me.submitPurchase(); });
        var canP = $id('cancelPurchaseBtn');
        if (canP) canP.addEventListener('click', function () { $id('purchaseForm').style.display = 'none'; });
        var apf = $id('applyPurchaseFilterBtn');
        if (apf) apf.addEventListener('click', function () {
            me.renderPurchases($id('purchaseProductSearch').value, $id('purchaseFromDateFilter').value, $id('purchaseToDateFilter').value);
        });
        var rpf = $id('resetPurchaseFilterBtn');
        if (rpf) rpf.addEventListener('click', function () {
            $id('purchaseProductSearch').value = '';
            $id('purchaseFromDateFilter').value = '';
            $id('purchaseToDateFilter').value = '';
            jalaliSync();
            me.renderPurchases();
        });

        document.addEventListener('click', function (e) {
            var t = e.target.closest('.view-purchase-invoice');
            if (t) me.openPurchaseInvoice(Number(t.getAttribute('data-id')));
            var p = e.target.closest('.print-sale-invoice');
            if (p) me.openSaleInvoice(Number(p.getAttribute('data-id')));
            var c = e.target.closest('.print-check');
            if (c) me.printCheck(Number(c.getAttribute('data-id')));
        });

        // بستن باکس‌ها با دکمه‌های close-detail-btn
        document.querySelectorAll('.close-detail-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var target = btn.getAttribute('data-target');
                if (target) {
                    var el = $id(target);
                    if (el) el.style.display = 'none';
                } else {
                    var box = btn.closest('[class*="-detail-box"], .ticket-detail, [id$="Box"], .profile-detail-box');
                    if (box) box.style.display = 'none';
                }
            });
        });

        // ---------- فروش (فقط فیلتر و تاریخچه) ----------
        var asc = $id('applySaleFilter');
        if (asc) asc.addEventListener('click', function () {
            me.renderOrders($id('saleSearchInvoice').value, $id('saleSearchName').value, $id('saleFromDate').value, $id('saleToDate').value);
        });
        var rsc = $id('resetSaleFilter');
        if (rsc) rsc.addEventListener('click', function () {
            $id('saleSearchInvoice').value = '';
            $id('saleSearchName').value = '';
            $id('saleFromDate').value = '';
            $id('saleToDate').value = '';
            jalaliSync();
            me.renderOrders();
        });

        // ---------- مشتریان ----------
        var sac = $id('showAddCustomerBtn');
        if (sac) {
            sac.addEventListener('click', function () {
                var form = $id('addCustomerForm');
                var open = form.style.display !== 'block';
                sac.textContent = open ? 'بستن فرم' : 'افزودن مشتری جدید';
                sac.innerHTML = '';
                sac.appendChild(document.createTextNode(open ? '✕ بستن فرم' : '+ افزودن مشتری جدید'));
                form.style.display = open ? 'block' : 'none';
                me._resetCustomerUIPrices();
                if (open) form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            });
        }
        document.addEventListener('input', function (e) {
            var inp = e.target.closest ? e.target.closest('.price-grid-input') : null;
            if (!inp || inp.closest('#modalPriceGrid')) return;
            var pid = Number(inp.getAttribute('data-id'));
            var v = Number(inp.value) || 0;
            var row = inp.closest('.price-grid-row');
            if (v > 0 && me.productsById[pid]) {
                me.pendingCustomerPrices[pid] = { name: me.productsById[pid].name, price: v };
                if (row) row.classList.add('filled');
            } else {
                delete me.pendingCustomerPrices[pid];
                if (row) row.classList.remove('filled');
            }
        });
        document.addEventListener('change', function (e) {
            var t = e.target.closest ? e.target.closest('.modal-discount-toggle') : null;
            if (!t) return;
            var row = t.closest('.price-grid-row');
            if (!row) return;
            var di = row.querySelector('.modal-discount-input');
            if (di) {
                di.disabled = !t.checked;
                if (!t.checked) di.value = '';
            }
        });
        var snc = $id('saveNewCustomerBtn');
        if (snc) snc.addEventListener('click', function () { me.submitNewCustomer(); });
        var cac = $id('cancelAddCustomerBtn');
        if (cac) cac.addEventListener('click', function () { $id('addCustomerForm').style.display = 'none'; });

        var scc = $id('searchCustomerBtn');
        if (scc) scc.addEventListener('click', function () { me.renderCustomerList($id('customerSearchInput').value); });
        var sperson = $id('personSearchInput'); // (گزارش اشخاص)
        var sci = $id('customerSearchInput');

        document.addEventListener('click', function (e) {
            var vc = e.target.closest('.view-customer');
            if (vc) me.openCustomerProfile(Number(vc.getAttribute('data-id')));
            var mc = e.target.closest('.msg-customer');
            if (mc) me.openCustomerMsgModal(Number(mc.getAttribute('data-id')));
            var dc = e.target.closest('.view-customer-debt');
            if (dc) me.openCustomerDebt(Number(dc.getAttribute('data-id')));
            var sp = e.target.closest('.set-customer-price');
            if (sp) me.openSetPriceModal(Number(sp.getAttribute('data-id')));
        });

        var cpb = $id('closeProfileBtn');
        if (cpb) cpb.addEventListener('click', function () { $id('customerProfileBox').style.display = 'none'; });

        // تب‌های پروفایل مشتری
        document.querySelectorAll('.profile-tabs .tab-btn').forEach(function (tb) {
            tb.addEventListener('click', function () {
                document.querySelectorAll('.profile-tabs .tab-btn').forEach(function (x) { x.classList.remove('active'); });
                tb.classList.add('active');
                var tab = tb.getAttribute('data-tab');
                ['profile-info', 'profile-ledger', 'profile-checks'].forEach(function (id) {
                    var el = $id(id);
                    if (el) el.classList.toggle('active', tab === id);
                });
            });
        });
        var alf = $id('applyLedgerFilter');
        if (alf) alf.addEventListener('click', function () {
            if (me.activeCustomerId) me.renderLedger(me.activeCustomerId);
        });
        var rlf = $id('resetLedgerFilter');
        if (rlf) rlf.addEventListener('click', function () {
            $id('ledgerFromDate').value = '';
            $id('ledgerToDate').value = '';
            jalaliSync();
            if (me.activeCustomerId) me.renderLedger(me.activeCustomerId);
        });

        // ---------- تیکت‌ها ----------
        var nt = $id('newTicketBtn');
        if (nt) {
            nt.addEventListener('click', function () {
                var form = $id('ticketForm');
                var open = form.style.display !== 'block';
                form.style.display = open ? 'block' : 'none';
                if (open) form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            });
        }
        var st = $id('submitTicketBtn');
        if (st) st.addEventListener('click', function () { me.submitNewTicket(); });
        var ct = $id('cancelTicketBtn');
        if (ct) ct.addEventListener('click', function () { $id('ticketForm').style.display = 'none'; });

        document.addEventListener('click', function (e) {
            var vt = e.target.closest('.view-ticket');
            if (vt) me.openTicket(Number(vt.getAttribute('data-id')));
            var at = e.target.closest('.answer-ticket');
            if (at) {
                me.activeTicketId = Number(at.getAttribute('data-id'));
                me.openTicketReplyModal();
            }
            var clt = e.target.closest('.close-ticket');
            if (clt) me.closeTicket(Number(clt.getAttribute('data-id')));
        });

        var cd = $id('closeDetailBtn');
        if (cd) cd.addEventListener('click', function () { $id('ticketDetail').style.display = 'none'; });

        var atf = $id('applyTicketFilter');
        if (atf) atf.addEventListener('click', function () {
            me.renderTickets($id('ticketTypeFilter').value, $id('ticketStatusFilter').value, $id('ticketSearchName').value);
        });
        var rtf = $id('resetTicketFilter');
        if (rtf) rtf.addEventListener('click', function () {
            $id('ticketTypeFilter').value = 'all';
            $id('ticketStatusFilter').value = 'all';
            $id('ticketSearchName').value = '';
            me.renderTickets();
        });

        // پاسخ به تیکت (مودال)
        var srm = $id('sendReplyModalBtn');
        if (srm) srm.addEventListener('click', function () { me.sendTicketReply(); });
        var crm = $id('cancelReplyModalBtn');
        if (crm) crm.addEventListener('click', function () { $id('ticketReplyModal').style.display = 'none'; });
        var rmr = $id('replyModalText');
        if (rmr) rmr.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) me.sendTicketReply();
        });

        // ---------- چک‌ها ----------
        var sac2 = $id('showAddCheckBtn');
        if (sac2) {
            sac2.addEventListener('click', function () {
                var form = $id('addCheckForm');
                if (!form) return;
                var open = !form.classList.contains('active');
                var toggleBtn = $id('showAddCheckBtn');
                if (toggleBtn) toggleBtn.innerHTML = open ? '<i class="fas fa-check"></i> بستن فرم' : '<i class="fas fa-plus"></i> افزودن چک جدید';
                form.classList.toggle('active', open);
                if (open) {
                    var today = new Date();
                    var plus30 = new Date(today.getTime() + 30 * 86400000);
                    var rd = $id('checkReceiveDate');
                    var dd = $id('checkDueDate');
                    if (rd) rd.value = isoDate(today);
                    if (dd) dd.value = isoDate(plus30);
                    jalaliSync();
                    var mb = $id('addCheckMsg');
                    if (mb) mb.innerHTML = '';
                    var fl = $id('checkFileList');
                    if (fl) fl.innerHTML = '';
                    var fi = $id('checkFile');
                    if (fi) fi.value = '';
                    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        }
        var saveC = $id('saveCheckBtn');
        if (saveC) saveC.addEventListener('click', function () { me.submitCheck(); });
        var cancelC = $id('cancelAddCheckBtn');
        if (cancelC) cancelC.addEventListener('click', function () {
            var form = $id('addCheckForm');
            if (form) form.classList.remove('active');
            var toggleBtn = $id('showAddCheckBtn');
            if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-plus"></i> افزودن چک جدید';
        });
        var scf = $id('searchCheckBtn');
        if (scf) scf.addEventListener('click', function () {
            me.checksQuery = $id('checkSearchInput').value || '';
            me.checksPage = 1;
            me.renderChecks();
        });
        var csi = $id('checkSearchInput');
        if (csi) {
            csi.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    me.checksQuery = csi.value || '';
                    me.checksPage = 1;
                    me.renderChecks();
                }
            });
            csi.addEventListener('input', function () {
                if (!csi.value) {
                    me.checksQuery = '';
                    me.checksPage = 1;
                    me.renderChecks();
                }
            });
        }
        var cf = $id('checkFile');
        if (cf) cf.addEventListener('change', function () {
            var list = $id('checkFileList');
            if (!list) return;
            list.innerHTML = '';
            var files = cf.files || [];
            if (files.length) {
                var names = [];
                for (var fi2 = 0; fi2 < files.length; fi2++) names.push(esc(files[fi2].name));
                list.innerHTML = '<div class="check-file-name">📎 ' + names.join(', ') + '</div>';
            }
        });

        // ---------- ارتباط با مشتریان (پیامک + یادآوری) ----------
        var sss = $id('sendSingleSmsBtn');
        if (sss) sss.addEventListener('click', function () {
            var d = $id('singleSmsDialog');
            var b = $id('bulkSmsDialog');
            if (b) b.classList.remove('active');
            if (d) {
                d.classList.toggle('active');
                var r = $id('singleSmsResult');
                if (r) r.innerHTML = '';
            }
        });
        var sbs = $id('sendBulkSmsBtn');
        if (sbs) sbs.addEventListener('click', function () {
            var d = $id('bulkSmsDialog');
            var s = $id('singleSmsDialog');
            if (s) s.classList.remove('active');
            if (d) {
                d.classList.toggle('active');
                var r = $id('bulkSmsResult');
                if (r) r.innerHTML = '';
            }
        });
        var srb = $id('setReminderBtn');
        if (srb) srb.addEventListener('click', function () {
            var w = $id('reminderTableWrap');
            if (!w) return;
            var open = w.style.display !== 'block';
            w.style.display = open ? 'block' : 'none';
            if (open) {
                me.renderReminderCustomerSelect();
                me.loadReminders();
                w.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
        var css1 = $id('closeSingleSmsDialog');
        if (css1) css1.addEventListener('click', function () { $id('singleSmsDialog').classList.remove('active'); });
        var ccs1 = $id('cancelSingleSmsDialog');
        if (ccs1) ccs1.addEventListener('click', function () { $id('singleSmsDialog').classList.remove('active'); });
        var css2 = $id('closeBulkSmsDialog');
        if (css2) css2.addEventListener('click', function () { $id('bulkSmsDialog').classList.remove('active'); });
        var ccs2 = $id('cancelBulkSmsDialog');
        if (ccs2) ccs2.addEventListener('click', function () { $id('bulkSmsDialog').classList.remove('active'); });
        var ssa = $id('sendSingleSmsBtnAction');
        if (ssa) ssa.addEventListener('click', function () { me.sendSingleSms(); });
        var sba = $id('sendBulkSmsBtnAction');
        if (sba) sba.addEventListener('click', function () { me.sendBulkSms(); });
        var svr = $id('saveReminderBtn');
        if (svr) svr.addEventListener('click', function () { me.submitReminder(); });
        document.addEventListener('click', function (e) {
            var dn = e.target.closest('.done-reminder');
            if (dn) me.doneReminder(Number(dn.getAttribute('data-id')), dn.getAttribute('data-done') === '1');
            var dr = e.target.closest('.delete-reminder');
            if (dr && confirm('آیا از حذف این یادآوری مطمئن هستید؟')) me.deleteReminder(Number(dr.getAttribute('data-id')));
            var mn = e.target.closest('.mark-notif-read');
            if (mn) me.markNotificationRead(Number(mn.getAttribute('data-id')));
        });

        // ---------- گزارشات ----------
        document.querySelectorAll('.person-sub-tabs .sub-tab-btn').forEach(function (tb) {
            tb.addEventListener('click', function () {
                document.querySelectorAll('.person-sub-tabs .sub-tab-btn').forEach(function (x) { x.classList.remove('active'); });
                tb.classList.add('active');
                document.querySelectorAll('.person-sub-content').forEach(function (c) { c.classList.remove('active'); });
                var el = $id(tb.getAttribute('data-subtab'));
                if (el) el.classList.add('active');
            });
        });
        var spb = $id('searchPersonBtn');
        if (spb) spb.addEventListener('click', function () { me.searchPeople($id('personSearchInput').value); });
        var psi = $id('personSearchInput');
        if (psi) psi.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') me.searchPeople(psi.value);
        });
        var cpd = $id('closePersonDetail');
        if (cpd) cpd.addEventListener('click', function () {
            var box = $id('personDetailBox');
            if (box) box.classList.remove('active');
        });
        var apf = $id('applyPurchaseFilter');
        if (apf) apf.addEventListener('click', function () { me.reloadPersonForActiveTab(); });
        var rpf = $id('resetPurchaseFilter');
        if (rpf) rpf.addEventListener('click', function () {
            $id('purchaseFromDate').value = '';
            $id('purchaseToDate').value = '';
            jalaliSync();
            me.reloadPersonForActiveTab();
        });
        var aif = $id('applyItemsFilter');
        if (aif) aif.addEventListener('click', function () {
            me.renderPersonItems($id('itemsFromDate').value, $id('itemsToDate').value);
        });
        var rif = $id('resetItemsFilter');
        if (rif) rif.addEventListener('click', function () {
            $id('itemsFromDate').value = '';
            $id('itemsToDate').value = '';
            jalaliSync();
            me.renderPersonItems('', '');
        });
        var aipf = $id('applyInvoicePersonFilter');
        if (aipf) aipf.addEventListener('click', function () { me.reloadPersonForActiveTab(); });
        var ripf = $id('resetInvoicePersonFilter');
        if (ripf) ripf.addEventListener('click', function () {
            $id('invoicePersonFromDate').value = '';
            $id('invoicePersonToDate').value = '';
            jalaliSync();
            me.reloadPersonForActiveTab();
        });
        var pis = $id('personInvoiceSearch');
        if (pis) pis.addEventListener('input', function () {
            me.renderPersonInvoices((me.reportState.person && me.reportState.person.invoices) || []);
        });
        var pps = $id('personProductSearch');
        if (pps) pps.addEventListener('input', function () {
            me.renderPersonInvoices((me.reportState.person && me.reportState.person.invoices) || []);
        });
        var dl = $id('debtorList');
        if (dl) dl.addEventListener('click', function (e) {
            var btn = e.target.closest('.view-debtor');
            if (btn) me.openDebtorDetail(Number(btn.getAttribute('data-id')));
        });
        var adf = $id('applyDebtorFilter');
        if (adf) adf.addEventListener('click', function () {
            var from = $id('debtorFromDate').value;
            var to = $id('debtorToDate').value;
            if (from && to && from > to) { me.reportMsg('⚠️ تاریخ شروع نباید از تاریخ پایان بزرگتر باشد.', 'error'); return; }
            me.loadDebtorsReport(from, to, me.reportState.debtorSearch);
        });
        var rdf = $id('resetDebtorFilter');
        if (rdf) rdf.addEventListener('click', function () {
            $id('debtorFromDate').value = '';
            $id('debtorToDate').value = '';
            jalaliSync();
            me.loadDebtorsReport('', '', me.reportState.debtorSearch);
        });
        var ads = $id('applyDebtorSearch');
        if (ads) ads.addEventListener('click', function () {
            me.reportState.debtorSearch = $id('debtorSearchInput').value.trim();
            me.loadDebtorsReport($id('debtorFromDate').value, $id('debtorToDate').value, me.reportState.debtorSearch);
        });
        var dsi = $id('debtorSearchInput');
        if (dsi) dsi.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                me.reportState.debtorSearch = dsi.value.trim();
                me.loadDebtorsReport($id('debtorFromDate').value, $id('debtorToDate').value, me.reportState.debtorSearch);
            }
        });
        var rds = $id('resetDebtorSearch');
        if (rds) rds.addEventListener('click', function () {
            $id('debtorSearchInput').value = '';
            me.reportState.debtorSearch = '';
            me.loadDebtorsReport($id('debtorFromDate').value, $id('debtorToDate').value, '');
        });
        var dp = $id('debtorPagination');
        if (dp) dp.addEventListener('click', function (e) {
            var btn = e.target.closest('button[data-page]');
            if (!btn) return;
            var page = Number(btn.getAttribute('data-page'));
            if (!page || page === me.reportState.debtorPage) return;
            me.reportState.debtorPage = page;
            me.renderDebtorsReport({
                total_debtors: me.reportState.debtors.length,
                total_debt_amount: me.reportState.debtors.reduce(function (s, d) { return s + Number(d.total_debt || 0); }, 0)
            });
        });
        var aff = $id('applyFinancialFilter');
        if (aff) aff.addEventListener('click', function () {
            me.financialState.period = $id('financialPeriod').value;
            me.financialState.from = $id('financialFrom').value;
            me.financialState.to = $id('financialTo').value;
            me.financialState.customerName = $id('financeCustomerSearch').value.trim();
            me.financialState.invoiceNumber = $id('financeInvoiceSearch').value.trim();
            me.loadFinancialData();
        });
        var rff = $id('resetFinancialFilter');
        if (rff) rff.addEventListener('click', function () {
            $id('financialPeriod').value = 'month';
            $id('financialFrom').value = '';
            $id('financialTo').value = '';
            $id('financeCustomerSearch').value = '';
            $id('financeInvoiceSearch').value = '';
            me.financialState = { period: 'month', from: '', to: '', granularity: me.financialState.granularity, customerName: '', invoiceNumber: '' };
            jalaliSync();
            me.loadFinancialData();
        });
        var fcs = $id('financeCustomerSearch');
        if (fcs) fcs.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { var b = $id('applyFinancialFilter'); if (b) b.click(); }
        });
        var fis = $id('financeInvoiceSearch');
        if (fis) fis.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { var b = $id('applyFinancialFilter'); if (b) b.click(); }
        });
        var efb = $id('exportFinancialBtn');
        if (efb) efb.addEventListener('click', function () { me.exportFinancialCsv(); });
        var vdb = $id('viewDebtorsBtn');
        if (vdb) vdb.addEventListener('click', function () {
            var box = $id('debtorBox');
            if (!box) return;
            box.classList.toggle('active');
            if (box.classList.contains('active')) {
                var dm = $id('debtorMsg');
                if (dm) dm.innerHTML = '';
                var sb = $id('settlementBox');
                if (sb) sb.classList.remove('active');
                if (me.financialData) me.renderFinancialDebtors(me.financialData.debtors);
            }
        });
        var cdb = $id('closeDebtorBtn');
        if (cdb) cdb.addEventListener('click', function () {
            var box = $id('debtorBox');
            if (box) box.classList.remove('active');
        });
        var vsb = $id('viewDistributorSettlementBtn');
        if (vsb) vsb.addEventListener('click', function () {
            var box = $id('settlementBox');
            if (!box) return;
            box.classList.toggle('active');
            if (box.classList.contains('active')) {
                var db = $id('debtorBox');
                if (db) db.classList.remove('active');
                var dm = $id('debtorMsg');
                if (dm) dm.innerHTML = '';
                if (me.financialData) me.renderFinancialSettlements(me.financialData.settlements);
            }
        });
        var csb = $id('closeSettlementBtn');
        if (csb) csb.addEventListener('click', function () {
            var box = $id('settlementBox');
            if (box) box.classList.remove('active');
        });
        var fcf = $id('financialChartFilter');
        if (fcf) fcf.addEventListener('change', function () {
            me.financialState.granularity = fcf.value;
            me.loadFinancialData();
        });

        jalaliEnhance();
        document.addEventListener('click', function () {
            document.querySelectorAll('.jcal-pop.open').forEach(function (pop) { pop.classList.remove('open'); });
        });

        // ---------- مانده حساب ----------
        var cbb = $id('closeCustomerBalanceBtn');
        if (cbb) cbb.addEventListener('click', function () { $id('customerBalanceBox').style.display = 'none'; });
        var cob = $id('closeCompanyBalanceBtn');
        if (cob) cob.addEventListener('click', function () { $id('companyBalanceBox').style.display = 'none'; });
        var abp = $id('applyBalanceProductFilter');
        if (abp) abp.addEventListener('click', function () {
            me.renderBalance($id('balanceProductSearch').value);
        });
        var rbp = $id('resetBalanceProductFilter');
        if (rbp) rbp.addEventListener('click', function () {
            $id('balanceProductSearch').value = '';
            me.renderBalance();
        });
        var acb = $id('applyCustomerBalanceFilter');
        if (acb) acb.addEventListener('click', function () {
            me.renderBalance($id('customerBalanceSearch').value, $id('customerBalanceFromDate').value, $id('customerBalanceToDate').value);
        });
        var rcb = $id('resetCustomerBalanceFilter');
        if (rcb) rcb.addEventListener('click', function () {
            $id('customerBalanceSearch').value = '';
            $id('customerBalanceFromDate').value = '';
            $id('customerBalanceToDate').value = '';
            jalaliSync();
            me.renderBalance();
        });
        var acob = $id('applyCompanyBalanceFilter');
        if (acob) acob.addEventListener('click', function () { me.renderBalance(); });
        var rcob = $id('resetCompanyBalanceFilter');
        if (rcob) rcob.addEventListener('click', function () { me.renderBalance(); });

        // ---------- تخفیف‌ها ----------
        var ad = $id('showAddDiscountBtn');
        if (ad) {
            ad.addEventListener('click', function () {
                var me2 = me;
                var form = $id('discountForm');
                if (!form) return;
                var open = form.style.display !== 'block';
                form.style.display = open ? 'block' : 'none';
                var tb = $id('showAddDiscountBtn');
                if (tb) tb.innerHTML = open ? '<i class="fas fa-x"></i> بستن فرم' : '<i class="fas fa-plus"></i> تخفیف جدید';
                if (open) {
                    me2.editingDiscountId = null;
                    var p = $id('discountProduct');
                    if (p) p.value = '';
                    var pc = $id('discountPercent');
                    if (pc) pc.value = '';
                    var cd = $id('discountCode');
                    if (cd) cd.value = '';
                    var sd2 = $id('discountStartDate');
                    var ed2 = $id('discountEndDate');
                    if (sd2) sd2.value = isoDate(new Date());
                    var plus30d = new Date(new Date().getTime() + 30 * 86400000);
                    if (ed2) ed2.value = isoDate(plus30d);
                    jalaliSync();
                    var m = $id('discountFormMsg');
                    if (m) m.innerHTML = '';
                    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        }
        var sd = $id('saveDiscountBtn');
        if (sd) sd.addEventListener('click', function () { me.submitDiscount(); });
        var cdd = $id('cancelDiscountBtn');
        if (cdd) cdd.addEventListener('click', function () {
            $id('discountForm').style.display = 'none';
            me.editingDiscountId = null;
            var tb = $id('showAddDiscountBtn');
            if (tb) tb.innerHTML = '<i class="fas fa-plus"></i> تخفیف جدید';
        });
        document.addEventListener('click', function (e) {
            var dd = e.target.closest('.delete-discount');
            if (dd && confirm('آیا از حذف این کد تخفیف مطمئن هستید؟')) me.deleteDiscount(Number(dd.getAttribute('data-id')));
        });

        // ---------- تنظیمات ----------
        var ep = $id('editProfileBtn');
        if (ep) ep.addEventListener('click', function () {
            var m = $id('profileModalResult');
            if (m) m.textContent = '';
            me.renderSettings();
            $id('profileModal').style.display = 'flex';
        });
        var sp = $id('saveProfileBtn');
        if (sp) sp.addEventListener('click', function () { me.saveProfile(); });
        var cp = $id('cancelProfileBtn');
        if (cp) cp.addEventListener('click', function () { $id('profileModal').style.display = 'none'; });
        var cpe = $id('changePasswordBtn');
        if (cpe) cpe.addEventListener('click', function () {
            $id('oldPassword').value = '';
            $id('newPassword').value = '';
            $id('confirmPassword').value = '';
            var m = $id('passwordModalResult');
            if (m) { m.textContent = ''; m.style.color = '#e74c3c'; }
            $id('passwordModal').style.display = 'flex';
        });
        var spw = $id('savePasswordBtn');
        if (spw) spw.addEventListener('click', function () { me.changePassword(); });
        var cpw = $id('cancelPasswordBtn');
        if (cpw) cpw.addEventListener('click', function () { $id('passwordModal').style.display = 'none'; });
        $id('cancelMsgBtn').addEventListener('click', function () { $id('customerMsgModal').style.display = 'none'; });
        var smg = $id('sendMsgBtn');
        if (smg) smg.addEventListener('click', function () { me.sendCustomerMsg(); });
        var cdm = $id('closeDebtModal');
        if (cdm) cdm.addEventListener('click', function () { $id('debtModal').style.display = 'none'; });

        var spm = $id('savePriceModalBtn');
        if (spm) spm.addEventListener('click', function () { me.saveCustPriceModal(); });
        document.addEventListener('click', function (e) {
            var dp = e.target.closest('.delete-modal-price');
            if (dp && confirm('آیا از حذف این قیمت دستی مطمئن هستید؟')) me.deleteModalPrice(Number(dp.getAttribute('data-id')));
        });
        var cpm = $id('cancelPriceModalBtn');
        if (cpm) cpm.addEventListener('click', function () { $id('setPriceModal').style.display = 'none'; });

        // نمایش/عدم نمایش رمزها
        document.querySelectorAll('.toggle-password').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var target = $id(btn.getAttribute('data-target'));
                if (!target) return;
                var isPassword = target.type === 'password';
                target.type = isPassword ? 'text' : 'password';
                btn.querySelector('i').className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
            });
        });

        // گزارشات: جستجوی اشخاص
        var sPerson = $id('searchPersonBtn');
        if (sPerson) {
            sPerson.addEventListener('click', function () {
                var q = ($id('personSearchInput').value || '').trim();
                var container = $id('personList');
                if (!container) return;
                var list = me.customers.filter(function (c) {
                    if (!q) return true;
                    return (c.full_name || c.company_name || c.username || '').indexOf(q) !== -1 ||
                        (c.phone || '').indexOf(q) !== -1 || (c.national_id || '').indexOf(q) !== -1;
                });
                if (!list.length) {
                    container.innerHTML = '<div class="person-card"><div class="name" style="opacity:0.6;">شخصی یافت نشد.</div></div>';
                    return;
                }
                container.innerHTML = list.map(function (c) {
                    var orders = me.orders.filter(function (o) { return o.customer === c.id; });
                    return '<div class="person-card" data-person="' + c.id + '">' +
                        '<div class="person-info"><div class="name">' + esc(c.full_name || c.company_name || c.username) + '</div>' +
                        '<div class="detail">' +
                        (c.phone ? '<span><i class="fas fa-phone"></i> ' + esc(c.phone) + '</span>' : '') +
                        (c.national_id ? '<span><i class="fas fa-id-card"></i> ' + esc(c.national_id) + '</span>' : '') +
                        '<span><i class="fas fa-shopping-cart"></i> ' + faNum(orders.length) + ' سفارش</span>' +
                        '<span><i class="fas fa-credit-card"></i> ' + toman(c.account_balance) + '</span>' +
                        '</div></div>' +
                        '<div><button class="btn-primary btn-sm view-person-report" data-id="' + c.id + '">مشاهده پرونده</button></div></div>';
                }).join('');
            });
        }
        document.addEventListener('click', function (e) {
            var vp = e.target.closest('.view-person-report');
            if (vp) me.loadPersonDetail(Number(vp.getAttribute('data-id')), '', '');
        });

        // تب‌های گزارشات
        document.querySelectorAll('.report-tabs .tab-btn').forEach(function (tb) {
            tb.addEventListener('click', function () {
                document.querySelectorAll('.report-tabs .tab-btn').forEach(function (x) { x.classList.remove('active'); });
                tb.classList.add('active');
                var tab = tb.getAttribute('data-tab');
                ['report-person', 'report-debtors', 'report-general', 'report-financial'].forEach(function (id) {
                    var el = $id(id);
                    if (el) el.classList.toggle('active', tab === id);
                });
                if (tab === 'report-person') me.loadPersonList();
                if (tab === 'report-debtors') me.loadDebtorsReport($id('debtorFromDate').value, $id('debtorToDate').value, me.reportState.debtorSearch || '');
                if (tab === 'report-general') me.loadGeneralReport();
                if (tab === 'report-financial') me.loadFinancialData();
            });
        });

        // گزارش بدهکاران (سرور) + خروجی عمومی
        var applyReportF = $id('applyReportFilter');
        if (applyReportF) applyReportF.addEventListener('click', function () { me.loadGeneralReport(); });
        var resetReportF = $id('resetReportFilter');
        if (resetReportF) resetReportF.addEventListener('click', function () {
            $id('reportFromDate').value = '';
            $id('reportToDate').value = '';
            var pf = $id('reportProductFilter');
            if (pf) pf.value = 'all';
            var in2 = $id('reportInvoiceNumber');
            if (in2) in2.value = '';
            var st2 = $id('reportSaleType');
            if (st2) st2.value = 'all';
            me.loadGeneralReport();
        });
        var exportExcel = $id('exportReportExcel');
        if (exportExcel) exportExcel.addEventListener('click', function () {
            me.exportGeneralCsv();
        });

        var closeDebtor = $id('closeDebtorDetail');
        if (closeDebtor) closeDebtor.addEventListener('click', function () {
            var box = $id('debtorDetailBox');
            if (box) box.classList.remove('active');
        });
    };

    // جستجوی مشتری با Enter
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            var t = e.target;
            if (t && t.id === 'customerSearchInput') {
                var panel = window.__distributorPanel;
                if (panel) panel.renderCustomerList(t.value);
            }
        }
    });

    // ================================================================
    // راه‌اندازی
    // ================================================================
    window.DistributorPanel = DistributorPanel;

    var started = false;
    var start = function () {
        if (started) return;
        started = true;
        var panel = new DistributorPanel();
        window.__distributorPanel = panel;
        panel.init();
    };

    document.addEventListener('DOMContentLoaded', start);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        start();
    }
})();
