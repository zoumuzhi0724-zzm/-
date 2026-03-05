from flask import Flask, request, jsonify, render_template
import hashlib
import time
import json

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
    
    def create_genesis_block(self):
        return Block(0, time.time(), {'message': 'Genesis Block'}, '0')
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)
    
    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

# 初始化区块链
blockchain = Blockchain()

# 创建Flask应用
app = Flask(__name__)

# 存储溯源数据的字典
traceability_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    product_id = data.get('product_id')
    product_name = data.get('product_name')
    manufacturer = data.get('manufacturer')
    production_date = data.get('production_date')
    
    # 创建产品信息
    product_info = {
        'product_id': product_id,
        'product_name': product_name,
        'manufacturer': manufacturer,
        'production_date': production_date,
        'status': '生产完成',
        'timestamp': time.time()
    }
    
    # 存储产品信息
    traceability_data[product_id] = product_info
    
    # 添加到区块链
    new_block = Block(
        len(blockchain.chain),
        time.time(),
        product_info,
        blockchain.get_latest_block().hash
    )
    blockchain.add_block(new_block)
    
    return jsonify({
        'message': '产品信息已添加到区块链',
        'block_hash': new_block.hash
    })

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    product_id = data.get('product_id')
    new_status = data.get('status')
    
    if product_id not in traceability_data:
        return jsonify({'error': '产品不存在'}), 404
    
    # 更新产品状态
    product_info = traceability_data[product_id]
    product_info['status'] = new_status
    product_info['timestamp'] = time.time()
    
    # 添加到区块链
    new_block = Block(
        len(blockchain.chain),
        time.time(),
        {
            'product_id': product_id,
            'status': new_status,
            'timestamp': time.time()
        },
        blockchain.get_latest_block().hash
    )
    blockchain.add_block(new_block)
    
    return jsonify({
        'message': '产品状态已更新并添加到区块链',
        'block_hash': new_block.hash
    })

@app.route('/api/trace/<product_id>', methods=['GET'])
def trace_product(product_id):
    if product_id not in traceability_data:
        return jsonify({'error': '产品不存在'}), 404
    
    product_info = traceability_data[product_id]
    
    # 查找与该产品相关的所有区块
    related_blocks = []
    for block in blockchain.chain:
        if isinstance(block.data, dict) and block.data.get('product_id') == product_id:
            related_blocks.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'data': block.data,
                'hash': block.hash,
                'previous_hash': block.previous_hash
            })
    
    return jsonify({
        'product_info': product_info,
        'blockchain_data': related_blocks
    })

@app.route('/api/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            'index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'hash': block.hash,
            'previous_hash': block.previous_hash
        })
    
    return jsonify({
        'chain': chain_data,
        'length': len(chain_data),
        'is_valid': blockchain.is_valid()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
