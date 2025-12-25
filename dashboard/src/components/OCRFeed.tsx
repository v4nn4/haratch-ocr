"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

// Maximum total characters to display in the feed history before flushing old lines
const MAX_CHARS = 2000;

interface OCRFeedProps {
    latestSnippet: string | null;
    currentPage: string | null;
}

export default function OCRFeed({ latestSnippet, currentPage }: OCRFeedProps) {
    const [displayLines, setDisplayLines] = useState<{ text: string, id: number, page: string }[]>([]);
    const [currentText, setCurrentText] = useState("");
    const snippetQueue = useRef<{ text: string, page: string }[]>([]);
    const isTyping = useRef(false);
    const lineIdCounter = useRef(0);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of feed
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [currentText, displayLines]);

    // When a new snippet arrives, add it to the queue if it's different from the last one
    useEffect(() => {
        if (latestSnippet && (snippetQueue.current.length === 0 || snippetQueue.current[snippetQueue.current.length - 1].text !== latestSnippet)) {
            snippetQueue.current.push({ text: latestSnippet, page: currentPage || "?" });
            if (!isTyping.current) {
                processQueue();
            }
        }
    }, [latestSnippet, currentPage]);

    const processQueue = async () => {
        if (snippetQueue.current.length === 0) {
            isTyping.current = false;
            return;
        }

        isTyping.current = true;
        const next = snippetQueue.current.shift()!;
        const text = next.text;

        // Type out the characters (Fast LLM style)
        let current = "";
        // Speed up for longer texts: more chars per tick if text is long
        const stepSize = Math.max(1, Math.floor(text.length / 200));

        for (let i = 0; i < text.length; i += stepSize) {
            current = text.substring(0, i + stepSize);
            setCurrentText(current);
            // Faster typing for "flow"
            await new Promise(r => setTimeout(r, 10 + Math.random() * 10));
        }

        // Ensure we show the full final text
        setCurrentText(text);
        await new Promise(r => setTimeout(r, 200));

        // Finished typing page
        setDisplayLines(prev => {
            const newLine = { text: text, id: lineIdCounter.current++, page: next.page };
            let newLines = [...prev, newLine];

            // Flush old lines if total character count exceeds MAX_CHARS
            let totalChars = newLines.reduce((sum, line) => sum + line.text.length, 0);
            while (totalChars > MAX_CHARS && newLines.length > 1) {
                totalChars -= newLines[0].text.length;
                newLines = newLines.slice(1);
            }

            return newLines;
        });
        setCurrentText("");

        // Pause before next page
        await new Promise(r => setTimeout(r, 500));
        processQueue();
    };

    return (
        <div className="bg-zinc-950 border border-zinc-800 rounded-sm overflow-hidden font-mono shadow-xl flex flex-col h-[400px]">
            <div className="bg-zinc-900/50 px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Terminal className="w-3 h-3 text-emerald-500" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Live OCR Feed (Armenian)</span>
                </div>
                <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-zinc-700" />
                    <div className="w-2 h-2 rounded-full bg-zinc-700" />
                    <div className="w-2 h-2 rounded-full bg-zinc-700" />
                </div>
            </div>

            <div
                ref={scrollRef}
                className="p-4 flex-1 overflow-y-auto scrollbar-hide flex flex-col gap-4 text-xs leading-relaxed"
            >
                {/* Past pages history */}
                {displayLines.map((line) => (
                    <div key={line.id} className="space-y-1 opacity-40">
                        <div className="flex items-center gap-2 text-zinc-600 select-none">
                            <span className="text-[9px] font-bold border border-zinc-800 px-1 rounded-sm uppercase tracking-tighter">PAGE {line.page}</span>
                            <div className="h-px flex-1 bg-zinc-900" />
                        </div>
                        <p className="text-zinc-500 italic whitespace-pre-wrap">{line.text}</p>
                    </div>
                ))}

                {/* Current streaming page */}
                {currentText && (
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-emerald-900 select-none">
                            <span className="text-[9px] font-bold border border-emerald-900/30 px-1 rounded-sm uppercase tracking-tighter bg-emerald-500/5 text-emerald-500">STREAMING {currentPage}</span>
                            <div className="h-px flex-1 bg-emerald-900/20" />
                        </div>
                        <div className="text-emerald-400 whitespace-pre-wrap">
                            {currentText}
                            <span className="inline-block w-1.5 h-3.5 bg-emerald-500 ml-1 animate-pulse" />
                        </div>
                    </div>
                )}

                {displayLines.length === 0 && !currentText && (
                    <div className="h-full flex flex-col items-center justify-center space-y-2 opacity-20">
                        <Terminal className="w-8 h-8 animate-pulse text-zinc-500" />
                        <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em]">Ready for stream</p>
                    </div>
                )}
            </div>

            <div className="px-4 py-1.5 bg-emerald-500/5 border-t border-emerald-500/10 flex justify-between items-center">
                <span className="text-[9px] text-emerald-500/50 font-bold uppercase tracking-widest animate-pulse">Connection Active</span>
                <span className="text-[9px] text-zinc-600 font-mono uppercase">{snippetQueue.current.length} blocks queued</span>
            </div>
        </div>
    );
}
