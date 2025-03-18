import React, { useState } from 'react';
import { Row, Col } from 'antd';
import RecognitionForm from '../components/recognition/RecognitionForm';
import RecognitionResults from '../components/recognition/RecognitionResults';
import ReviewInterface from '../components/review/ReviewInterface';

const RecognitionPage = () => {
  const [workflowResult, setWorkflowResult] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);
  const [showReview, setShowReview] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [workflowId, setWorkflowId] = useState(null);
  
  const handleRecognitionComplete = (result) => {
    setWorkflowResult(result);
    setIsProcessing(false);
    
    // Generate a workflow ID from timestamp if not provided
    if (result && !workflowId) {
      setWorkflowId(result.recognition?.recognition?.metadata?.image_hash || `workflow_${Date.now()}`);
    }
    
    // Automatically show review if needed
    if (result?.next_step === 'human_review') {
      setShowReview(true);
    } else {
      setShowReview(false);
    }
  };
  
  const handleProcessingStart = () => {
    setIsProcessing(true);
    setWorkflowResult(null);
    setShowReview(false);
  };
  
  const handleRequestReview = () => {
    setShowReview(true);
  };
  
  const handleReviewComplete = (updatedResult) => {
    setWorkflowResult(updatedResult);
    setShowReview(false);
  };
  
  const handleImageCapture = (imageUrl) => {
    setOriginalImage(imageUrl);
  };
  
  return (
    <div className="recognition-page">
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <RecognitionForm 
            onRecognitionComplete={handleRecognitionComplete}
            onProcessingStart={handleProcessingStart}
            onImageCapture={handleImageCapture}
          />
        </Col>
        
        <Col xs={24} lg={12}>
          {showReview ? (
            <ReviewInterface 
              workflowResult={workflowResult}
              workflowId={workflowId}
              onReviewComplete={handleReviewComplete}
            />
          ) : (
            <RecognitionResults 
              result={workflowResult}
              originalImage={originalImage}
              onRequestReview={handleRequestReview}
              isLoading={isProcessing}
            />
          )}
        </Col>
      </Row>
    </div>
  );
};

export default RecognitionPage;
