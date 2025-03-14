import os
import zipfile
import tempfile
import requests
import json
import time

# 配置
API_URL = "http://localhost:8011/api"
USERNAME = "testuser"  # 测试用户
PASSWORD = "testpassword"  # 测试密码

# 临时测试文件内容
TEST_FILES = {
    "index.html": "<html><body><h1>测试项目</h1></body></html>",
    "styles.css": "body { font-family: Arial; color: #333; }",
    "script.js": "console.log('Hello, World!');"
}

def get_token():
    """获取认证令牌"""
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        
        if response.status_code != 200:
            print(f"登录失败: {response.text}")
            return None
        
        data = response.json()
        print(f"登录成功! 获取到令牌: {data['access_token'][:10]}...")
        return data["access_token"]
    except Exception as e:
        print(f"登录过程中发生错误: {str(e)}")
        return None

def create_test_project(token):
    """创建测试项目"""
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "name": "测试上传项目",
        "description": "用于测试文件上传功能",
        "project_type": "frontend"
    }
    
    response = requests.post(
        f"{API_URL}/projects/",
        json=project_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"创建项目失败: {response.text}")
        return None
    
    project = response.json()
    print(f"创建项目成功: {project['name']} (ID: {project['id']})")
    return project["id"]

def create_test_zip():
    """创建测试ZIP文件"""
    tmp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    
    with zipfile.ZipFile(tmp_file.name, 'w') as zipf:
        for filename, content in TEST_FILES.items():
            zipf.writestr(filename, content)
    
    print(f"创建测试ZIP文件: {tmp_file.name}")
    return tmp_file.name

def upload_project_files(token, project_id, zip_path, mode="replace"):
    """上传项目文件"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(zip_path, 'rb') as zip_file:
        files = {'file': ('test.zip', zip_file, 'application/zip')}
        data = {'mode': mode}
        
        try:
            response = requests.post(
                f"{API_URL}/projects/upload/{project_id}",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"上传文件失败: {response.status_code} - {response.reason}")
                try:
                    print(f"错误详情: {response.json()}")
                except:
                    print(f"错误响应: {response.text}")
                return False
            
            print("上传文件成功!")
            return True
        except Exception as e:
            print(f"上传过程中发生错误: {str(e)}")
            return False

def check_project_files(token, project_id):
    """检查项目文件列表"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/projects/{project_id}/files",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"获取文件列表失败: {response.text}")
        return None
    
    files_data = response.json()
    print("\n项目文件列表:")
    print(f"当前路径: {files_data['current_path']}")
    print("\n文件:")
    for file in files_data["files"]:
        print(f" - {file['name']} ({file['size']} 字节)")
    
    return files_data

def main():
    """主函数"""
    print("====== 开始测试文件上传功能 ======")
    
    # 获取认证令牌
    token = get_token()
    if not token:
        return
    
    # 创建测试项目
    project_id = create_test_project(token)
    if not project_id:
        return
    
    # 创建测试ZIP文件
    zip_path = create_test_zip()
    
    try:
        # 上传项目文件
        if not upload_project_files(token, project_id, zip_path):
            return
        
        # 检查项目文件
        files_data = check_project_files(token, project_id)
        if not files_data:
            return
        
        # 检查是否存在我们上传的文件
        file_names = [f["name"] for f in files_data["files"]]
        expected_files = TEST_FILES.keys()
        
        missing_files = [f for f in expected_files if f not in file_names]
        if missing_files:
            print(f"\n警告: 以下文件在服务器上未找到: {missing_files}")
        else:
            print("\n✅ 所有文件上传成功!")
        
    finally:
        # 清理临时文件
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"已删除临时ZIP文件: {zip_path}")
    
    print("\n====== 测试完成 ======")

if __name__ == "__main__":
    main() 