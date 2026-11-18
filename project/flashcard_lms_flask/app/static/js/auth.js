
// 1. Lấy ô nhập mật khẩu từ HTML
const passwordInput = document.getElementById("password");

// 2. Lấy nút hiện/ẩn mật khẩu từ HTML
const toggleButton = document.getElementById("togglePassword");

// 3. Kiểm tra hai phần tử có tồn tại hay không
if (passwordInput && toggleButton) {

    // 4. Lắng nghe sự kiện click trên nút
    toggleButton.addEventListener("click", function () {

        // 5. Kiểm tra trạng thái hiện tại của ô mật khẩu
        const isPassword = passwordInput.type === "password";

        // 6. Thay đổi kiểu hiển thị
        passwordInput.type = isPassword ? "text" : "password";

        // 7. Đổi nội dung nút
        toggleButton.textContent = isPassword ? "Ẩn" : "Hiện";

        // 8. Cập nhật mô tả hỗ trợ truy cập
        toggleButton.setAttribute(
            "aria-label",
            isPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"
        );
    });
}
