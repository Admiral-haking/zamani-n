// ========================================
// ZAMANI AUTH - نسخه نهایی با کنترل قیمت‌ها
// ========================================

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", loginUser);
    }

    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", registerUser);
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function(e) {
            e.preventDefault();
            if (confirm('آیا از خروج از حساب کاربری مطمئن هستید؟')) {
                logout();
            }
        });
    }

    // ===== نمایش یا مخفی کردن قیمت‌ها =====
    togglePrices();
});

// ========================================
// نمایش یا مخفی کردن قیمت‌ها
// ========================================

function togglePrices() {
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('zamaniCurrentUser') || '{}');
    const isLoggedIn = !!(token && user.loggedIn);
    // قیمت‌ها فقط زمانی قابل مشاهده‌اند که کاربر وارد شده باشد
    // و صراحتاً پیش‌تر «مخفی» نکرده باشد (zamaniSavedInfo === '0')
    const savedInfo = localStorage.getItem('zamaniSavedInfo');
    const canSee = isLoggedIn && savedInfo !== '0';

    // قیمت‌ها
    document.querySelectorAll('.price-hidden').forEach(el => {
        if (canSee) {
            el.classList.add('price-visible');
        } else {
            el.classList.remove('price-visible');
        }
    });

    // دکمه‌های نمایش قیمت
    document.querySelectorAll('.price-toggle-btn').forEach(btn => {
        if (canSee) {
            btn.classList.add('is-visible');
            btn.innerHTML = '<i class="fas fa-eye"></i>';
            btn.title = 'قیمت‌ها قابل مشاهده هستند';
        } else {
            btn.classList.remove('is-visible');
            btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            btn.title = isLoggedIn ? 'قیمت‌ها مخفی شده‌اند' : 'برای مشاهده قیمت لاگین کنید';
        }
    });

    console.log('💰 وضعیت قیمت‌ها:', canSee ? 'نمایش' : 'مخفی');
}

// ========================================
// ذخیره خودکار قیمت‌های تعیین‌شده بعد از ورود
// (بدون هیچ پیغام/کارتی — بلافاصله بعد از لاگین یا ثبت‌نام)
// ========================================

async function saveAssignedPrices(role) {
    // ۱) از این پس قیمت‌ها برای این کاربر نمایش داده می‌شوند
    localStorage.setItem('zamaniSavedInfo', '1');
    // ۲) دیگر هیچ پرامپتی برای «می‌خواهید قیمت‌ها را ببینید؟» نشان داده نمی‌شود
    localStorage.removeItem('zz_pending_save_prompt');

    try {
        let priceList = null;
        const r = String(role || 'CUSTOMER').toUpperCase();

        if (r === 'CUSTOMER') {
            // قیمت‌های تعیین‌شده مشتری (price_list پروفایل او)
            let res = null;
            try {
                res = await apiGet('customers/');
            } catch (e) {
                res = null;
            }
            let c = res && res.success ? res.data : null;
            if (Array.isArray(c)) c = c[0];
            else if (c && Array.isArray(c.results)) c = c.results[0];
            if (c && c.price_list) priceList = c.price_list;
        } else if (r === 'DISTRIBUTOR') {
            // قیمت‌های فروشگاه خودِ پخش‌کننده
            const res = await apiGet('pricing/?page_size=500');
            const rows = res && res.success ? res.data : null;
            const list = Array.isArray(rows) ? rows
                : (rows && Array.isArray(rows.results)) ? rows.results : [];
            const map = {};
            list.forEach(function(row) {
                const pid = row.product != null ? row.product : row.product_id;
                if (pid != null) map[pid] = Number(row.price || 0);
            });
            priceList = map;
        }

        // ۳) سیو قیمت‌های تعیین‌شده در localStorage (همان چیزی که قبلاً با «بله» ذخیره می‌شد)
        if (priceList && typeof priceList === 'object' && Object.keys(priceList).length) {
            localStorage.setItem('zamaniSavedPriceList', JSON.stringify(priceList));
            console.log('💰 قیمت‌های تعیین‌شده ذخیره شدند');
        }
    } catch (e) {
        console.warn('⚠️ خطا در ذخیره قیمت‌های تعیین‌شده:', e);
    }
}

// ========================================
// هدایت بر اساس نقش
// ========================================

function redirectBasedOnRole(role) {
    console.log('🔄 هدایت بر اساس نقش:', role);
    const userRole = String(role).toUpperCase();
    
    switch(userRole) {
        case 'ADMIN':
            window.location.href = "sab.html";
            break;
        case 'SECRETARY':
            // v=3: جلوگیری از کش نسخه قدیمی پنل منشی در مرورگر
            window.location.href = "monshi.html?v=3";
            break;
        case 'CUSTOMER':
            window.location.href = "dashbord.html";
            break;
        case 'DISTRIBUTOR':
            window.location.href = "pakhsh.html";
            break;
        default:
            window.location.href = "index.html";
    }
}

// ========================================
// LOGIN
// ========================================

async function loginUser(event) {
    event.preventDefault();

    const username = document.getElementById("loginUsername")?.value?.trim() || "";
    const password = document.getElementById("loginPassword")?.value?.trim() || "";

    if (!username || !password) {
        showAlert("❌ نام کاربری و رمز عبور را وارد کنید", "error");
        return;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ در حال ورود...';
    }

    try {
        const result = await apiPost("accounts/login/", {
            username: username,
            password: password
        });

        console.log("📡 LOGIN RESPONSE:", result);

        if (result.success) {
            // ذخیره توکن
            if (result.data?.access) {
                localStorage.setItem('access_token', result.data.access);
                localStorage.setItem('refresh_token', result.data.refresh);
                console.log("✅ توکن ذخیره شد");
            }

            // دریافت نقش
            let userRole = 'CUSTOMER';
            if (result.data?.user?.role) {
                userRole = result.data.user.role;
                console.log("👤 نقش کاربر از پاسخ لاگین:", userRole);
            } else {
                try {
                    const profileResponse = await apiGet("accounts/me/");
                    if (profileResponse.success && profileResponse.data) {
                        userRole = profileResponse.data.role || 'CUSTOMER';
                        console.log("👤 نقش کاربر از me/:", userRole);
                    }
                } catch (e) {
                    console.warn("⚠️ خطا در دریافت پروفایل:", e);
                }
            }

            // ذخیره اطلاعات کاربر
            const userInfo = {
                username: username,
                role: userRole,
                loggedIn: true
            };
            localStorage.setItem('zamaniCurrentUser', JSON.stringify(userInfo));
            localStorage.setItem('zamaniUserLoggedIn', 'true');

            // ===== قفل قیمت فقط برای مهمان: از این لحظه قیمت‌ها نمایش داده می‌شوند =====
            // ذخیره خودکار قیمت‌های تعیین‌شده بدون هیچ پیغامی
            saveAssignedPrices(userRole);

            showAlert(`✅ ورود موفق! خوش آمدید ${username}`, "success");

            // ===== نمایش قیمت‌ها بعد از لاگین =====
            togglePrices();

            // هدایت با تأخیر
            setTimeout(() => {
                redirectBasedOnRole(userRole);
            }, 500);

        } else {
            showAlert(`❌ ${result.data?.detail || 'نام کاربری یا رمز عبور اشتباه است'}`, "error");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'ورود به حساب کاربری';
            }
        }
    } catch (error) {
        console.error("❌ Error in login:", error);
        showAlert("❌ خطا در ارتباط با سرور", "error");
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'ورود به حساب کاربری';
        }
    }
}

// ========================================
// REGISTER (ثبت‌نام عمومی)
// ========================================

const REG_SUCCESS_MESSAGE = "درخواست ثبت نام شما ثبت شد نام کاربری و رمز عبور بزودی برای شما از طریق پیامک ارسال خواهد شد";

function extractApiError(result) {
    const d = result && result.data;
    if (!d) return "خطا در ارتباط با سرور";
    if (typeof d === "string") return d;
    if (d.error) return d.error;
    if (d.detail) return d.detail;
    for (const key of Object.keys(d)) {
        const v = d[key];
        if (Array.isArray(v) && v.length) return String(v[0]);
        if (typeof v === "string" && v) return v;
    }
    return "خطا در ثبت درخواست";
}

// سرویس پیامک هنوز در backend فعال نشده است؛ از نمایش موفقیت جعلی جلوگیری می‌کنیم.
window.sendRegistrationOtp = async function () {
    showAlert("ℹ️ سرویس پیامک هنوز پیکربندی نشده است؛ درخواست شما پس از ثبت توسط منشی بررسی می‌شود.", "info");
};

// بررسی کد تایید وارد‌شده
window.verifyRegistrationOtp = async function () {
    showAlert("ℹ️ تایید پیامکی در این محیط فعال نیست؛ شماره تماس توسط منشی بررسی می‌شود.", "info");
};

async function registerUser(event) {
    event.preventDefault();

    const firstName = document.getElementById("regFirstName")?.value?.trim() || "";
    const lastName = document.getElementById("regLastName")?.value?.trim() || "";
    const phone = document.getElementById("regPhone")?.value?.trim() || "";
    const nationalId = document.getElementById("regNationalId")?.value?.trim() || "";
    const shopName = document.getElementById("regShopName")?.value?.trim() || "";
    const postalCode = document.getElementById("regPostalCode")?.value?.trim() || "";
    const address = document.getElementById("regAddress")?.value?.trim() || "";
    const referral = document.getElementById("regReferralCode")?.value?.trim() || "";
    const terms = document.getElementById("termsCheckbox");

    if (!firstName || !lastName || !phone || !nationalId || !shopName || !postalCode || !address) {
        showAlert("❌ لطفاً همه فیلدهای الزامی را پر کنید", "error");
        return;
    }
    if (!/^09[0-9]{9}$/.test(phone)) {
        showAlert("❌ شماره تماس باید با 09 شروع و 11 رقم باشد", "error");
        return;
    }
    if (!/^[0-9]{10}$/.test(nationalId)) {
        showAlert("❌ کد ملی باید ۱۰ رقم باشد", "error");
        return;
    }
    if (!/^[0-9]{10}$/.test(postalCode)) {
        showAlert("❌ کد پستی باید ۱۰ رقم باشد", "error");
        return;
    }
    if (terms && !terms.checked) {
        showAlert("❌ برای ثبت نام، قوانین و شرایط را بپذیرید", "error");
        return;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ در حال ثبت درخواست...';
    }

    try {
        const result = await apiPost("tickets/guest-request/", {
            guest_name: `${firstName} ${lastName}`.trim(),
            guest_phone: phone,
            title: `درخواست ایجاد حساب - ${shopName}`,
            message: `کد ملی: ${nationalId}\nنام فروشگاه: ${shopName}\nکد پستی: ${postalCode}\nآدرس: ${address}\nکد معرف: ${referral || "ثبت نشده"}`
        });

        if (result.success) {
            showAlert("✅ " + REG_SUCCESS_MESSAGE, "success");
            event.target.reset();
            window.__regPhoneVerified = false;
            if (window.__regOtp) window.__regOtp.clear();
            const status = document.getElementById("otpStatus");
            if (status) {
                status.textContent = "📲 ابتدا شماره موبایل را وارد و کد تایید را دریافت کنید";
                status.style.color = "";
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'ثبت نام در زامنی برگر';
            }
        } else {
            showAlert("❌ " + extractApiError(result), "error");
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'ثبت نام در زامنی برگر';
            }
        }
    } catch (error) {
        console.error("❌ Error in register:", error);
        showAlert("❌ خطا در ارتباط با سرور", "error");
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'ثبت نام در زامنی برگر';
        }
    }
}

// ========================================
// HELPERS
// ========================================

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('zamaniCurrentUser');
    localStorage.removeItem('zamaniUserLoggedIn');
    // قیمت‌های سیو‌شده‌ی کاربر قبلی نباید برای بعدی بماند
    localStorage.removeItem('zamaniSavedPriceList');
    localStorage.removeItem('zz_pending_save_prompt');

    // ===== مخفی کردن قیمت‌ها بعد از خروج =====
    togglePrices();
    
    showAlert("👋 خارج شدید", "info");
    setTimeout(() => {
        window.location.href = "log.html";
    }, 300);
}

function showAlert(message, type = 'info') {
    const oldAlert = document.querySelector('.custom-alert');
    if (oldAlert) oldAlert.remove();

    const colors = { success: '#2ecc71', error: '#e74c3c', info: '#3498db', warning: '#f1c40f' };

    const alert = document.createElement('div');
    alert.className = 'custom-alert';
    alert.style.cssText = `
        position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
        padding: 16px 28px; background: ${colors[type] || '#3498db'};
        color: white; border-radius: 12px; font-size: 15px;
        z-index: 999999; max-width: 90%; text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        animation: slideDown 0.4s ease; direction: rtl;
        font-family: 'Vazir', sans-serif;
    `;
    alert.textContent = message;

    if (!document.getElementById('alertStyles')) {
        const style = document.createElement('style');
        style.id = 'alertStyles';
        style.textContent = `
            @keyframes slideDown {
                from { opacity: 0; transform: translateX(-50%) translateY(-30px); }
                to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                if (alert.parentNode) alert.remove();
            }, 300);
        }
    }, 4000);
}

// ========================================
// شنود تغییرات localStorage برای به‌روزرسانی قیمت‌ها
// ========================================

window.addEventListener('storage', function(e) {
    if (e.key === 'access_token' || e.key === 'zamaniCurrentUser' || e.key === 'zamaniUserLoggedIn') {
        togglePrices();
    }
});

// ========================================
// اجرا مجدد قیمت‌ها وقتی صفحه لود شد
// ========================================

if (document.readyState === 'complete') {
    togglePrices();
} else {
    document.addEventListener('DOMContentLoaded', togglePrices);
}
