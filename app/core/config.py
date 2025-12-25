from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    
    # Gán giá trị mặc định (phòng hờ Docker chưa truyền vào kịp)
    SECRET_KEY: str = "AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-GGGG"
    
    # QUAN TRỌNG: Phải gán giá trị mặc định chuỗi kết nối DB
    # Để nếu không tìm thấy biến môi trường, nó sẽ dùng cái này.
    DATABASE_URL: str = "mysql+pymysql://root:Mysql%402025@db:3306/production_management"

    class Config:
        env_file = ".env"
        # Bỏ qua các biến thừa trong file .env để đỡ lỗi
        extra = "ignore" 

settings = Settings()