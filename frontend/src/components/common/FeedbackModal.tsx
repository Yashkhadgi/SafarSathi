import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, CheckCircle2, AlertCircle, X } from 'lucide-react';
import { apiPost } from '../../api/client';

interface FeedbackModalProps {
  messageId?: string;
  conversationId?: string;
  initialRating?: number;
  onClose: () => void;
  onSubmitted?: () => void;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  messageId,
  conversationId,
  initialRating = 1,
  onClose,
  onSubmitted,
}) => {
  const [rating, setRating] = useState<number>(initialRating);
  const [reason, setReason] = useState<string>('other');
  const [comment, setComment] = useState<string>('');
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiPost('/feedback', {
        message_id: messageId || null,
        conversation_id: conversationId || null,
        rating,
        reason: rating < 0 ? reason : null,
        comment: comment || null,
      });
      setSubmitted(true);
      setTimeout(() => {
        if (onSubmitted) onSubmitted();
        onClose();
      }, 1500);
    } catch {
      // Ignore submission error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-sm rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <span className="text-xs font-semibold text-white">Assistant Turn Feedback</span>
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {submitted ? (
          <div className="py-6 text-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <p className="text-xs font-medium text-white">Thank you for your feedback!</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center justify-center gap-4">
              <button
                type="button"
                onClick={() => setRating(1)}
                className={`p-3 rounded-md border flex flex-col items-center gap-1 transition-colors ${
                  rating > 0
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                <ThumbsUp className="w-5 h-5" />
                <span className="text-[10px] font-medium">Helpful</span>
              </button>

              <button
                type="button"
                onClick={() => setRating(-1)}
                className={`p-3 rounded-md border flex flex-col items-center gap-1 transition-colors ${
                  rating < 0
                    ? 'bg-red-950/80 border-red-700 text-red-300'
                    : 'bg-slate-950 border-slate-800 text-slate-500'
                }`}
              >
                <ThumbsDown className="w-5 h-5" />
                <span className="text-[10px] font-medium">Not Helpful</span>
              </button>
            </div>

            {rating < 0 && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="fb-reason">
                  Reason Code
                </label>
                <select
                  id="fb-reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-brand-500"
                >
                  <option value="wrong_info">Inaccurate facts / Wrong information</option>
                  <option value="too_long">Too verbose / repetitive</option>
                  <option value="language_error">Language translation mistake</option>
                  <option value="other">Other issue</option>
                </select>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="fb-comment">
                Additional Notes (Optional)
              </label>
              <textarea
                id="fb-comment"
                rows={2}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="What could be improved?"
                className="w-full px-2.5 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:border-brand-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded-md bg-slate-800 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-1.5 rounded-md bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium cursor-pointer"
              >
                {loading ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
