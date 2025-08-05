/**
 * Automotive OBD Diagnostic Component
 * Japanese interface for automotive diagnostics
 */

import React, { useState } from 'react';
import { Button, Form, Input, Select, Card, Typography, Table, Tag, Alert } from 'antd';
import { CarOutlined, ToolOutlined, SearchOutlined, UploadOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface OBDCode {
  code: string;
  description: string;
  type: string;
  severity: string;
}

interface DiagnosticArticle {
  article_id: string;
  summary: string;
  obd_codes: OBDCode[];
  vehicle_info?: {
    make: string;
    model: string;
    year: number;
  };
  diagnostic_category?: string;
  score: number;
}

const AutomotiveDiagnostic: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [searchResults, setSearchResults] = useState<DiagnosticArticle[]>([]);
  const [chatResponse, setChatResponse] = useState<string>('');

  // Vehicle makes for Japanese market
  const vehicleMakes = [
    'Honda', 'Toyota', 'Nissan', 'Mazda', 'Subaru', 'Suzuki', 'Mitsubishi'
  ];

  const handleOBDAnalysis = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/automotive/analyze-obd-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      const result = await response.json();
      setAnalysisResult(result);
    } catch (error) {
      console.error('OBD分析エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnosticSearch = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/automotive/search-diagnostics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      const result = await response.json();
      setSearchResults(result.articles || []);
    } catch (error) {
      console.error('診断検索エラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutomotiveChat = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/automotive/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: values.message })
      });
      const result = await response.json();
      setChatResponse(result.response);
    } catch (error) {
      console.error('チャットエラー:', error);
    } finally {
      setLoading(false);
    }
  };

  const obdCodeColumns = [
    {
      title: 'コード',
      dataIndex: 'code',
      key: 'code',
      render: (code: string) => <Tag color="blue">{code}</Tag>
    },
    {
      title: '説明',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'タイプ',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const color = type === 'P' ? 'red' : type === 'C' ? 'orange' : 'green';
        return <Tag color={color}>{type}</Tag>;
      }
    },
    {
      title: '重要度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => {
        const color = severity === 'High' ? 'red' : severity === 'Medium' ? 'orange' : 'green';
        return <Tag color={color}>{severity}</Tag>;
      }
    }
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>
        <CarOutlined /> 自動車OBD診断システム
      </Title>
      <Text type="secondary">
        Goo-net Pit対応の日本車診断プラットフォーム
      </Text>

      {/* OBD Code Analysis Section */}
      <Card 
        title={<><ToolOutlined /> OBDコード分析</>}
        style={{ marginTop: '24px' }}
      >
        <Form
          onFinish={handleOBDAnalysis}
          layout="vertical"
        >
          <Form.Item
            name="obd_code"
            label="OBDコード"
            rules={[{ required: true, message: 'OBDコードを入力してください' }]}
          >
            <Input 
              placeholder="例: U3003-1C, P0171, C1AE687"
              style={{ fontSize: '16px' }}
            />
          </Form.Item>

          <Form.Item name="vehicle_make" label="車両メーカー">
            <Select placeholder="メーカーを選択（任意）" allowClear>
              {vehicleMakes.map(make => (
                <Option key={make} value={make}>{make}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="vehicle_model" label="車種">
            <Input placeholder="例: N-BOX, プリウス, セレナ" />
          </Form.Item>

          <Form.Item name="vehicle_year" label="年式">
            <Input type="number" placeholder="例: 2020" />
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={loading}>
            分析開始
          </Button>
        </Form>

        {analysisResult && (
          <Alert
            style={{ marginTop: '16px' }}
            message="分析結果"
            description={analysisResult.analysis}
            type="info"
            showIcon
          />
        )}
      </Card>

      {/* Diagnostic Search Section */}
      <Card 
        title={<><SearchOutlined /> 診断情報検索</>}
        style={{ marginTop: '24px' }}
      >
        <Form
          onFinish={handleDiagnosticSearch}
          layout="vertical"
        >
          <Form.Item
            name="query"
            label="検索キーワード"
            rules={[{ required: true, message: '検索キーワードを入力してください' }]}
          >
            <Input 
              placeholder="例: パワーステアリング, エンジン警告灯, ブレーキ"
            />
          </Form.Item>

          <Form.Item name="vehicle_make" label="車両メーカー">
            <Select placeholder="メーカーで絞り込み（任意）" allowClear>
              {vehicleMakes.map(make => (
                <Option key={make} value={make}>{make}</Option>
              ))}
            </Select>
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={loading}>
            検索実行
          </Button>
        </Form>

        {searchResults.length > 0 && (
          <div style={{ marginTop: '24px' }}>
            <Title level={4}>検索結果 ({searchResults.length}件)</Title>
            {searchResults.map((article, index) => (
              <Card 
                key={article.article_id}
                size="small"
                style={{ marginBottom: '12px' }}
                title={`記事 ${article.article_id}`}
                extra={<Tag color="blue">スコア: {article.score?.toFixed(2)}</Tag>}
              >
                <Text>{article.summary}</Text>
                {article.vehicle_info && (
                  <div style={{ marginTop: '8px' }}>
                    <Tag color="green">
                      {article.vehicle_info.make} {article.vehicle_info.model} ({article.vehicle_info.year})
                    </Tag>
                  </div>
                )}
                {article.obd_codes && article.obd_codes.length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    {article.obd_codes.map((code, i) => (
                      <Tag key={i} color="red">{code.code}</Tag>
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* Automotive AI Chat Section */}
      <Card 
        title="自動車AI診断チャット"
        style={{ marginTop: '24px' }}
      >
        <Form
          onFinish={handleAutomotiveChat}
          layout="vertical"
        >
          <Form.Item
            name="message"
            label="質問・相談内容"
            rules={[{ required: true, message: '質問を入力してください' }]}
          >
            <TextArea 
              rows={4}
              placeholder="例: N-BOXのパワーステアリング警告灯が点灯しました。どうすればよいでしょうか？"
            />
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={loading}>
            相談する
          </Button>
        </Form>

        {chatResponse && (
          <Card 
            title="AI診断アドバイス"
            style={{ marginTop: '16px' }}
            bodyStyle={{ backgroundColor: '#f6ffed' }}
          >
            <Text style={{ whiteSpace: 'pre-wrap' }}>{chatResponse}</Text>
          </Card>
        )}
      </Card>
    </div>
  );
};

export default AutomotiveDiagnostic;