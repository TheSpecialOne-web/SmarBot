#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertisseur CSV vers JSON pour le chatbot Goo-net Pit
Transforme les données CSV en format JSON structuré pour l'IA automotive
"""

import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoonetDataConverter:
    """Convertisseur principal pour les données Goo-net Pit"""
    
    def __init__(self):
        self.obd_patterns = {
            # Codes OBD standards avec descriptions en japonais
            'U3003': '12Vバッテリ 電圧値異常',
            'P0171': 'システムがリーンすぎる（バンク1）',
            'C1AE687': 'ABSモジュール通信エラー',
            'B1342': 'エアコンコンプレッサークラッチ回路異常',
            'P0300': 'ランダム失火検出',
            'P0420': '触媒効率低下（バンク1）',
            'P0455': '燃料蒸発システム大リーク検出',
            'C1201': 'エンジンECU通信異常'
        }
        
        self.car_manufacturers = {
            'ホンダ': ['N-BOX', 'フィット', 'ヴェゼル', 'フリード', 'ステップワゴン'],
            'トヨタ': ['プリウス', 'アクア', 'ヴィッツ', 'カローラ', 'ハリアー'],
            '日産': ['セレナ', 'ノート', 'エクストレイル', 'リーフ', 'マーチ'],
            'マツダ': ['デミオ', 'CX-5', 'アクセラ', 'アテンザ', 'ロードスター'],
            'スバル': ['インプレッサ', 'フォレスター', 'レガシィ', 'XV', 'BRZ']
        }

    def extract_obd_codes(self, text: str) -> List[Dict[str, str]]:
        """テキストからOBDコードを抽出"""
        codes = []
        # OBDコードのパターン (例: U3003-1C, P0171, C1AE687)
        obd_pattern = r'([PCBU][0-9A-F]{4}(?:-[0-9A-F]{1,2})?)'
        
        matches = re.finditer(obd_pattern, text)
        for match in matches:
            code = match.group(1)
            base_code = code.split('-')[0]  # -1C などのサフィックスを除去
            description = self.obd_patterns.get(base_code, '不明なコード')
            
            codes.append({
                'code': code,
                'description': description,
                'position': match.start()
            })
        
        return codes

    def extract_vehicle_info(self, text: str) -> Dict[str, Any]:
        """テキストから車両情報を抽出"""
        vehicle_info = {
            'manufacturer': None,
            'model': None,
            'year': None,
            'full_name': None
        }
        
        # 年式の抽出 (例: 2017年、（2020）)
        year_pattern = r'[\(（]?(\d{4})[\)）]?年?'
        year_match = re.search(year_pattern, text)
        if year_match:
            vehicle_info['year'] = int(year_match.group(1))
        
        # メーカーとモデルの抽出
        for manufacturer, models in self.car_manufacturers.items():
            if manufacturer in text:
                vehicle_info['manufacturer'] = manufacturer
                for model in models:
                    if model in text:
                        vehicle_info['model'] = model
                        # フルネームの抽出 (例: ホンダ・N-BOXカスタム)
                        full_name_pattern = f'{manufacturer}[・·]([^（\\(\\s]+)'
                        full_match = re.search(full_name_pattern, text)
                        if full_match:
                            vehicle_info['full_name'] = f"{manufacturer}・{full_match.group(1)}"
                        break
                break
        
        return vehicle_info

    def extract_symptoms_and_diagnosis(self, text: str) -> Dict[str, str]:
        """症状と診断を抽出"""
        result = {
            'symptom': None,
            'diagnosis': None,
            'solution': None
        }
        
        # 症状のキーワード
        symptom_patterns = [
            r'(警告灯が点灯|エアコンが効かない|失火|異音|振動|ハンドルが重い)',
            r'(冷却性能が低下|エンジンが不調|ブレーキに異常)'
        ]
        
        for pattern in symptom_patterns:
            match = re.search(pattern, text)
            if match:
                result['symptom'] = match.group(1)
                break
        
        # 診断結果の抽出
        if 'この故障コードは' in text:
            diagnosis_start = text.find('この故障コードは')
            diagnosis_end = text.find('。', diagnosis_start)
            if diagnosis_end > diagnosis_start:
                result['diagnosis'] = text[diagnosis_start:diagnosis_end + 1]
        
        # 対処法の抽出
        if '対処法' in text or '修理' in text:
            solution_start = max(text.find('対処法'), text.find('修理'))
            result['solution'] = text[solution_start:].strip()
        
        return result

    def convert_diagnostic_articles(self, csv_file: str) -> List[Dict[str, Any]]:
        """診断記事CSVをJSON形式に変換"""
        logger.info(f"診断記事の変換開始: {csv_file}")
        
        df = pd.read_csv(csv_file)
        articles = []
        
        for _, row in df.iterrows():
            # OBDコード抽出
            obd_codes = self.extract_obd_codes(row['text'])
            
            # 車両情報抽出
            vehicle_info = self.extract_vehicle_info(row['text'])
            
            # 症状・診断抽出
            symptoms_diagnosis = self.extract_symptoms_and_diagnosis(row['text'])
            
            # 推定価格と時間の抽出
            price_pattern = r'(\d+[,，]\d+|\d+)円?'
            time_pattern = r'(\d+(?:\.\d+)?)[‐-]?(\d+(?:\.\d+)?)時間'
            
            price_match = re.search(price_pattern, row['text'])
            time_match = re.search(time_pattern, row['text'])
            
            estimated_price = None
            estimated_duration = None
            
            if price_match:
                price_str = price_match.group(1).replace(',', '').replace('，', '')
                estimated_price = int(price_str)
            
            if time_match:
                # 時間範囲の場合は平均を取る
                time1 = float(time_match.group(1))
                time2 = float(time_match.group(2)) if time_match.group(2) else time1
                estimated_duration = (time1 + time2) / 2
            
            article = {
                'article_id': str(row['article_id']),
                'create_time': row['create_time'],
                'category_id': row['category_id'],
                'vehicle_info': vehicle_info,
                'obd_codes': obd_codes,
                'symptom': symptoms_diagnosis['symptom'],
                'diagnosis': symptoms_diagnosis['diagnosis'],
                'solution': symptoms_diagnosis['solution'],
                'estimated_price': estimated_price,
                'estimated_duration': estimated_duration,
                'full_text': row['text'],
                'summary': row['summary'],
                'article_length': row['article_length']
            }
            
            articles.append(article)
        
        logger.info(f"変換完了: {len(articles)}件の記事を処理")
        return articles

    def generate_garage_data(self) -> List[Dict[str, Any]]:
        """サンプルガレージデータを生成 (実際のCSVがある場合は読み込み処理に変更)"""
        logger.info("ガレージデータの生成開始")
        
        sample_garages = [
            {
                'garage_id': '0123456',
                'nom': 'GOOD UP 株式会社',
                'adresse': '北海道旭川市神楽5条11丁目2−3',
                'services': ['車検', 'パーツ取付', '修理', 'OBD診断'],
                'ville': '旭川市',
                'prefecture': '北海道',
                'url_blog': 'https://www.goo-net.com/pit/shop/0123456/blog/',
                'specialites': ['ホンダ', 'トヨタ'],
                'horaires': '9:00-18:00',
                'telephone': '0166-23-4567'
            },
            {
                'garage_id': '0234567',
                'nom': 'カーメンテナンス東京',
                'adresse': '東京都世田谷区三軒茶屋2-15-8',
                'services': ['車検', '修理', '板金塗装', 'タイヤ交換'],
                'ville': '世田谷区',
                'prefecture': '東京都',
                'url_blog': 'https://www.goo-net.com/pit/shop/0234567/blog/',
                'specialites': ['日産', 'マツダ'],
                'horaires': '8:30-19:00',
                'telephone': '03-3412-5678'
            },
            {
                'garage_id': '0345678',
                'nom': 'オートサービス大阪',
                'adresse': '大阪府大阪市中央区難波3-7-12',
                'services': ['修理', 'パーツ取付', 'OBD診断', 'エアコン修理'],
                'ville': '大阪市',
                'prefecture': '大阪府',
                'url_blog': 'https://www.goo-net.com/pit/shop/0345678/blog/',
                'specialites': ['スバル', 'ホンダ'],
                'horaires': '9:00-17:30',
                'telephone': '06-6212-3456'
            }
        ]
        
        logger.info(f"ガレージデータ生成完了: {len(sample_garages)}件")
        return sample_garages

    def convert_and_save_all(self, 
                           csv_file: str = '/workspaces/SmarBot/sample_automotive_data.csv',
                           output_dir: str = '/workspaces/SmarBot/data/json'):
        """すべてのデータを変換してJSONファイルに保存"""
        
        # 出力ディレクトリを作成
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 診断記事の変換
        articles = self.convert_diagnostic_articles(csv_file)
        articles_file = Path(output_dir) / 'diagnostic_articles.json'
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"診断記事保存完了: {articles_file}")
        
        # ガレージデータの生成
        garages = self.generate_garage_data()
        garages_file = Path(output_dir) / 'garages.json'
        with open(garages_file, 'w', encoding='utf-8') as f:
            json.dump(garages, f, ensure_ascii=False, indent=2)
        logger.info(f"ガレージデータ保存完了: {garages_file}")
        
        # 統計情報の表示
        total_obd_codes = sum(len(article['obd_codes']) for article in articles)
        vehicles_with_info = sum(1 for article in articles if article['vehicle_info']['manufacturer'])
        
        print(f"\n🚗 データ変換完了サマリー:")
        print(f"  📄 診断記事: {len(articles)}件")
        print(f"  🔧 ガレージ: {len(garages)}件")
        print(f"  🚨 OBDコード検出: {total_obd_codes}件")
        print(f"  🚙 車両情報抽出: {vehicles_with_info}件")
        print(f"  📁 出力先: {output_dir}")
        
        return {
            'articles': articles,
            'garages': garages,
            'stats': {
                'total_articles': len(articles),
                'total_garages': len(garages),
                'obd_codes_found': total_obd_codes,
                'vehicles_identified': vehicles_with_info
            }
        }

if __name__ == '__main__':
    converter = GoonetDataConverter()
    result = converter.convert_and_save_all()
    print("\n✅ 変換処理が完了しました！")
