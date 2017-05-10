# Hướng dẫn cài đặt

## Chuẩn bị môi trường
- Đảm bảo rằng dịch vụ ssh đang chạy trên các máy sử dụng
	+ Linux: openssh-server
	+ Windows: Bitvise SSH Server 7.29, tạo virtual account và đặt mật khẩu.

--> Chú ý: hiện nay tài khoản để ssh đang bị fix cứng là daidv, password 1.

Tương lai, có 2 hướng để cải tiến: cấu hình tài khoản và password hoặc sử dụng private/public key
## Cài đặt trên Linux
- Các gói phụ thuộc: 
	+ sudo apt-get install putty-tools=0.67-2
	+ sudo pip install watchdog==0.8.3
- Cấu hình file syncit.cfg
- Chạy chương trình:
	+ Role server: python monitor.py -ip 192.168.122.1 -port 8081 -uname daidv -role server
	+ Role client: python monitor.py -ip 192.168.122.1 -port 8082 -uname daidv -role client
## Cài đặt trên Windows

- Các gói phụ thuộc:
	+ Tải pscp.exe và đặt ở thư mục ổ C
	+ sudo pip install watchdog==0.8.3
- Cấu hình và chạy chương trình tương tự.
	+ Chú ý 1: đường dẫn trên Windows có khác biệt
		+ ví dụ: dir1: C:\Users\BvSsh_VirtualUsers
	+ Chú ý 2: Thay thế pscp -> C:\pscp.exe trong hàm push_file ở client.py

## Thử nghiệm

- Tạo file mới ở thự mục của client, chỉnh sửa ... -> thấy kết quả ở thư mục của server

## Ghi chú

- Crtl + Z để tắt chương trình và chạy lệnh sau để kill chương trình (Lý do: hiện tại chưa có cơ chế tắt process khi Crt + C, sẽ implement sau)
	+ kill -9 $(ps aux | grep monitor.py | awk '{print $2}')