
// ========================================
// AUTHENTICATION - PASSWORD VISIBILITY
// ========================================

// Tìm tất cả các nút hiện/ẩn mật khẩu
const passwordToggleButtons = document.querySelectorAll(
    "[data-password-toggle]"
);

// Duyệt qua từng nút
passwordToggleButtons.forEach(function (button) {

    // Lấy ID của ô nhập mà nút này điều khiển
    const targetId = button.dataset.target;

    // Tìm ô nhập mật khẩu tương ứng
    const passwordInput = document.getElementById(targetId);

    // Nếu không tìm thấy ô nhập thì bỏ qua
    if (!passwordInput) {
        return;
    }

    // Lắng nghe sự kiện nhấn nút
    button.addEventListener("click", function () {

        // Kiểm tra ô nhập đang bị che hay đang hiển thị
        const isHidden = passwordInput.type === "password";

        // Thay đổi kiểu nhập liệu
        if (isHidden) {
            passwordInput.type = "text";
        } else {
            passwordInput.type = "password";
        }

        // Cập nhật trạng thái hỗ trợ truy cập
        button.setAttribute(
            "aria-label",
            isHidden ? "Ẩn mật khẩu" : "Hiện mật khẩu"
        );

        button.setAttribute(
            "aria-pressed",
            String(isHidden)
        );

        // Thay đổi biểu tượng
        const icon = button.querySelector("span");

        if (icon) {
            icon.textContent = isHidden ? "◎" : "◉";
        }
    });
});


// ========================================
// AUTHENTICATION - REGISTER VALIDATION
// ========================================

// Lấy biểu mẫu đăng ký
const registerForm = document.querySelector(".register-form");

if (registerForm) {

    // Lấy hai ô mật khẩu
    const password = document.getElementById("register_password");

    const confirmPassword = document.getElementById("confirm_password");

    // Kiểm tra khi gửi biểu mẫu
    registerForm.addEventListener("submit", function (event) {

        // Nếu không tìm thấy hai ô mật khẩu thì dừng
        if (!password || !confirmPassword) {
            return;
        }

        // So sánh mật khẩu
        if (password.value !== confirmPassword.value) {

            event.preventDefault();

            confirmPassword.setCustomValidity(
                "Mật khẩu xác nhận không khớp."
            );

            confirmPassword.reportValidity();

        } else {

            confirmPassword.setCustomValidity("");
        }
    });

    // Xóa thông báo lỗi khi người dùng sửa nội dung
    if (confirmPassword) {
        confirmPassword.addEventListener("input", function () {
            confirmPassword.setCustomValidity("");
        });
    }
}
