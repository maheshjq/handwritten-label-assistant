import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { InboxOutlined, LoadingOutlined } from '@ant-design/icons';
import { Card, Typography, Progress, Alert, Image } from 'antd';
import { toast } from 'react-toastify';

const { Text, Title } = Typography;

const ImageUploader = ({ onImageUpload, isLoading }) => {
  const [preview, setPreview] = useState(null);
  
  const onDrop = useCallback(acceptedFiles => {
    const file = acceptedFiles[0];
    if (!file) return;
    
    // Check file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }
    
    // Create preview
    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(file);
    
    // Pass the file to parent component
    onImageUpload(file);
  }, [onImageUpload]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    multiple: false,
    disabled: isLoading
  });
  
  return (
    <Card>
      <div 
        {...getRootProps()} 
        className={`upload-container ${isDragActive ? 'active' : ''} ${isLoading ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} />
        
        {isLoading ? (
          <div className="upload-loading">
            <LoadingOutlined style={{ fontSize: 36 }} />
            <Text>Processing image...</Text>
            <Progress percent={50} status="active" />
          </div>
        ) : preview ? (
          <div className="upload-preview">
            <Image src={preview} alt="Preview" style={{ maxHeight: 200 }} />
            <Text>Drop a new image to replace</Text>
          </div>
        ) : (
          <div className="upload-prompt">
            <InboxOutlined style={{ fontSize: 48 }} />
            <Title level={4}>
              {isDragActive 
                ? 'Drop the image here...' 
                : 'Drag & drop an image here, or click to select'}
            </Title>
            <Text type="secondary">
              Supports JPG, PNG, GIF, BMP, WEBP
            </Text>
          </div>
        )}
      </div>
      
      {preview && !isLoading && (
        <Alert 
          message="Image ready for processing" 
          description="Click 'Process Image' below to start handwriting recognition" 
          type="info" 
          showIcon 
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );
};

export default ImageUploader;
