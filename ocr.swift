import Vision
import AppKit
import Foundation

guard CommandLine.arguments.count == 2 else {
    print("用法: swift ocr.swift <图片路径>")
    exit(1)
}

let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cgImg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("无法读取图片: \(path)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImg, options: [:])
do {
    try handler.perform([request])
} catch {
    print("OCR 失败: \(error)")
    exit(1)
}

guard let results = request.results as? [VNRecognizedTextObservation] else {
    print("未识别到文字")
    exit(0)
}

for obs in results {
    if let candidate = obs.topCandidates(1).first {
        print(candidate.string)
    }
}
